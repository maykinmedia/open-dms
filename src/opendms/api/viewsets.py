from django.utils.translation import gettext_lazy as _

import structlog
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework.views import APIView
from zgw_consumers.constants import APITypes
from zgw_consumers.models import Service

from opendms.search_index.client import get_elasticsearch_client

from .clients import get_documenten_client, get_zaaktypen_client, get_zaken_client
from .models import ZGWApiGroupConfig
from .serializers import (
    DocumentSerializer,
    SearchSerializer,
    ServiceSerializer,
    ZaakSerializer,
    ZaakTypeSerializer,
)
from .typing import (
    DocumentsPaginatedResponse,
    DocumentType,
    PaginatedResponse,
    SearchParameters,
    Zaak,
    ZaakType,
    ZaakTypenPaginatedResponse,
    ZakenPaginatedResponse,
)
from .utils.mixins import ReadOnlyViewSetMixin
from .utils.pagination import CountedPagination
from .utils.schema import (
    DOCUMENT_PARAM,
    QUERY_PARAM,
    QUERY_PARAM_FIELD,
    SERVICE_PARAM,
    ZAAK_PARAM,
    ZAAKTYPE_PARAM,
    ZAAKTYPEN_ZAAKTYPE_UUID_PARAM,
    ZAKEN_ZAAK_UUID_PARAM,
    param,
)

logger = structlog.stdlib.get_logger(__name__)


class SearchView(APIView):
    # TODO make GET is not allowed
    # TODO check extend_schema
    @extend_schema(
        tags=["search"],
        summary=_("Search"),
        operation_id="search",
        description=_("Search the document records."),
        request=SearchSerializer,
        responses=DocumentSerializer(many=True),
    )
    def post(self, request, *args, **kwargs) -> DocumentsPaginatedResponse:
        query_serializer = SearchSerializer(data=request.data)
        query_serializer.is_valid(raise_exception=True)
        params: SearchParameters = query_serializer.validated_data

        # TODO check if params are required or not
        # TODO add test for the params
        with get_elasticsearch_client() as client:
            search_results = client.get_search_results(
                query=params["query"],
                creatiedatum_from=params["creatiedatum_vanaf"],
                creatiedatum_to=params["creatiedatum_tot_en_met"],
                page=params["page"],
                page_size=params["page_size"],
                sort=params["sort"],
            )

        results = [DocumentType(**record) for record in search_results.results]
        serializer = DocumentSerializer(results, many=True)
        return Response(
            PaginatedResponse(count=search_results.total_count, results=serializer.data)
        )


class ServiceViewSet(viewsets.ReadOnlyModelViewSet):
    filter_backends = (SearchFilter,)
    queryset = Service.objects.filter(api_type=APITypes.ztc)
    lookup_field = "slug"
    serializer_class = ServiceSerializer
    pagination_class = CountedPagination
    search_fields = ["slug", "api_root", "label"]


@extend_schema_view(
    list=extend_schema(
        summary="zaaktypenList",
        parameters=[SERVICE_PARAM, QUERY_PARAM],
    ),
    retrieve=extend_schema(
        summary="zaaktypenRetrieve",
        parameters=[SERVICE_PARAM, ZAAKTYPE_PARAM],
    ),
)
class ZaakTypeViewSet(ReadOnlyViewSetMixin, viewsets.ViewSet):
    """
    Exposes Zaaktypen from /services/<zgw-service>/zaaktypen
    """

    _service: Service | None = None
    _zgw_group: ZGWApiGroupConfig | None = None

    serializer_class = ZaakTypeSerializer
    pagination_class = CountedPagination
    lookup_field = "zaaktype_uuid"
    lookup_search_field = "identificatie__icontains"
    queryset = None

    def clean_search_field(self, params: dict) -> dict:
        query_params = params.copy()
        if query_params and QUERY_PARAM_FIELD in query_params.keys():
            param = query_params.get(QUERY_PARAM_FIELD)
            del query_params[QUERY_PARAM_FIELD]
            query_params[self.lookup_search_field] = param
        return query_params

    def get_object(self) -> ZaakType:
        """
        Retrieve a single ZaakType from the external service by UUID.

        This method is overridden because the ViewSet does not use a Django
        model or ORM queryset. Instead, the requested ZaakType is fetched
        directly from the external Zaaktypen API using the client.
        """
        uuid = self.kwargs.get(self.lookup_field)
        with get_zaaktypen_client(self.zgw_group.ztc_service) as client:
            return client.get_item_by_uuid(uuid)

    def get_paginated_queryset(self, params: dict) -> ZaakTypenPaginatedResponse:
        """
        Retrieve all Zaaktypen available for the configured service.

        This method is overridden because no Django model queryset exists.
        ZaakType data is retrieved dynamically from the external Zaaktypen
        API via the configured client.
        """
        params = self.clean_search_field(params)
        with get_zaaktypen_client(self.zgw_group.ztc_service) as client:
            return client.get_paginated_cached_items(self.service.slug, params)


@extend_schema_view(
    list=extend_schema(
        summary="zakenList",
        parameters=[
            SERVICE_PARAM,
            ZAAKTYPEN_ZAAKTYPE_UUID_PARAM,
            param(
                name="startdatum__gte",
                description=_(
                    "De datum waarop met de uitvoering van de zaak is gestart"
                ),
                type_param=OpenApiTypes.DATE,
            ),
            param(
                name="identificatie__icontains",
                description=_(
                    "De unieke identificatie van de ZAAK (bevat de identificatie de gegeven waarden (hoofdletterongevoelig))",
                ),
            ),
            param(
                name="omschrijving",
                description=_(
                    "Een korte omschrijving van de ZAAK (bevat de omschrijving de gegeven waarden (hoofdletterongevoelig))"
                ),
            ),
        ],
    ),
    retrieve=extend_schema(
        summary="zakenRetrieve",
        parameters=[SERVICE_PARAM, ZAAKTYPEN_ZAAKTYPE_UUID_PARAM, ZAAK_PARAM],
    ),
)
class ZaakViewSet(ReadOnlyViewSetMixin, viewsets.ViewSet):
    """
    Exposes Zaak from /services/<zgw-service>/zaaktypen/<zaaktype>/zaken
    """

    serializer_class = ZaakSerializer
    pagination_class = CountedPagination
    lookup_field = "zaak_uuid"
    parent_lookup_field = "zaaktypen_zaaktype_uuid"
    queryset = None
    _zaaktype_url = None

    @property
    def zaaktype_url(self) -> str:
        if not self._zaaktype_url:
            zaaktype_uuid = self.kwargs.get(self.parent_lookup_field)
            with get_zaaktypen_client(self.zgw_group.ztc_service) as client:
                # TODO investigate here if you can use cache
                zaaktype = client.get_item_by_uuid(zaaktype_uuid)
                return zaaktype["url"]
        return self._zaaktype_url

    def get_object(self) -> Zaak:
        """
        Retrieve a single Zaak from the external service by UUID.

        This method is overridden because the ViewSet does not use a Django
        model or ORM queryset. Instead, the requested Zaak is fetched
        directly from the external Zaken API using the client.
        """
        uuid = self.kwargs.get(self.lookup_field)
        with get_zaken_client(self.zgw_group.zrc_service) as client:
            return client.get_item_by_uuid(uuid)

    def get_paginated_queryset(self, params: dict) -> ZakenPaginatedResponse:
        """
        Retrieve all Zaken filtered by a specific Zaaktype.

        This method is overridden because no Django model queryset exists.
        Zaak data is retrieved dynamically from the external Zaken
        API via the configured client.
        """
        with get_zaken_client(self.zgw_group.zrc_service) as client:
            # TODO investigate here if you can use cache
            return client.get_paginated_items_by_zaaktype(self.zaaktype_url, params)


@extend_schema_view(
    list=extend_schema(
        summary="documentsList",
        parameters=[
            SERVICE_PARAM,
            ZAAKTYPEN_ZAAKTYPE_UUID_PARAM,
            ZAKEN_ZAAK_UUID_PARAM,
        ],
    ),
    retrieve=extend_schema(
        summary="documentsRetrieve",
        parameters=[
            SERVICE_PARAM,
            ZAAKTYPEN_ZAAKTYPE_UUID_PARAM,
            ZAKEN_ZAAK_UUID_PARAM,
            DOCUMENT_PARAM,
        ],
    ),
)
class DocumentViewSet(ReadOnlyViewSetMixin, viewsets.ViewSet):
    """
    Exposes Documents from /services/<zgw-service>/zaaktypen/<zaaktype>/zaken/<zaak>/documents
    """

    serializer_class = DocumentSerializer
    pagination_class = CountedPagination
    lookup_field = "document_uuid"
    parent_lookup_field = "zaken_zaak_uuid"
    queryset = None
    _zaak_url = None

    @property
    def zaak_url(self) -> str:
        if not self._zaak_url:
            zaak_uuid = self.kwargs.get(self.parent_lookup_field)
            with get_zaken_client(self.zgw_group.zrc_service) as client:
                # TODO investigate here if you can use cache
                zaak = client.get_item_by_uuid(zaak_uuid)
                return zaak["url"]
        return self._zaak_url

    def get_object(self) -> DocumentType | None:
        """
        Retrieve a single Document from the Elasticsearch index

        This method is overridden because the ViewSet does not use a Django
        model or ORM queryset. Instead, the requested Document is fetched
        directly from the external Elasticsearch index.
        """
        uuid = self.kwargs.get(self.lookup_field)
        with get_documenten_client(self.zgw_group.drc_service) as client:
            return client.get_item_by_uuid(uuid)

    def get_paginated_queryset(self, params: dict) -> DocumentsPaginatedResponse:
        """
        Retrieve all Documents filtered by a specific Zaak.

        This method is overridden because no Django model queryset exists.
        Document data is retrieved dynamically from the external Elasticsearch index
        API via the configured client.
        """
        with get_documenten_client(self.zgw_group.drc_service) as client:
            # TODO investigate here if you can use cache
            return client.get_paginated_items_by_zaak(self.zaak_url, params)

    @extend_schema(
        "document_download",
        summary="documentsDownload",
        description="Download de binaire data van het (ENKELVOUDIG) INFORMATIEOBJECT.",
        parameters=[
            SERVICE_PARAM,
            ZAAKTYPEN_ZAAKTYPE_UUID_PARAM,
            ZAKEN_ZAAK_UUID_PARAM,
            DOCUMENT_PARAM,
        ],
        responses={
            (status.HTTP_200_OK, "application/octet-stream"): OpenApiResponse(
                description="De binaire bestandsinhoud",
                response=OpenApiTypes.BINARY,
            )
        },
    )
    @action(methods=["get"], detail=True, name="document_download")
    def download(self, request, *args, **kwargs):
        uuid = self.kwargs.get(self.lookup_field)
        with get_documenten_client(self.zgw_group.drc_service) as client:
            return client.download_document(uuid)
