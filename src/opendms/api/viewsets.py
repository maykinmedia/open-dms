from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter
from vng_api_common.pagination import DynamicPageSizePagination
from zgw_consumers.constants import APITypes
from zgw_consumers.models import Service

from .clients import get_zaaktypen_client, get_zaken_client
from .models import ZGWApiGroupConfig
from .serializers import ServiceSerializer, ZaakSerializer, ZaakTypeSerializer
from .typing import ZaakAPI, ZaakTypeAPI
from .utils.mixins import ReadOnlyViewSetMixin

QUERY_PARAM_FIELD = "search"


class ServiceViewSet(viewsets.ReadOnlyModelViewSet):
    filter_backends = (SearchFilter,)
    queryset = Service.objects.filter(api_type=APITypes.ztc)
    lookup_field = "slug"
    pagination_class = DynamicPageSizePagination
    serializer_class = ServiceSerializer

    search_fields = ["slug", "api_root", "label"]


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                name="service_slug",
                type=str,
                location=OpenApiParameter.PATH,
                required=True,
            ),
            OpenApiParameter(
                name=QUERY_PARAM_FIELD,
                description=_(
                    "A search term for the ZaakType service. "
                    "The search is performed against the `identificatie__icontains` field."
                ),
                required=False,
                location=OpenApiParameter.QUERY,
                type=str,
            ),
        ],
    ),
    retrieve=extend_schema(
        parameters=[
            OpenApiParameter(
                name="service_slug",
                type=str,
                location=OpenApiParameter.PATH,
                required=True,
            ),
            OpenApiParameter(
                name="zaaktype_uuid",
                type=str,
                location=OpenApiParameter.PATH,
                required=True,
            ),
        ],
    ),
)
class ZaakTypeViewSet(ReadOnlyViewSetMixin, viewsets.ViewSet):
    """
    Exposes Zaaktypen from /services/<zgw-service>/zaaktypen
    """

    _service: Service | None = None
    _zgw_group: ZGWApiGroupConfig | None = None

    serializer_class = ZaakTypeSerializer
    pagination_class = DynamicPageSizePagination
    lookup_field = "zaaktype_uuid"
    search_field = "identificatie__icontains"
    queryset = None

    def get_object(self) -> ZaakTypeAPI | None:
        """
        Retrieve a single ZaakType from the external service by UUID.

        This method is overridden because the ViewSet does not use a Django
        model or ORM queryset. Instead, the requested ZaakType is fetched
        directly from the external Zaaktypen API using the client.
        """
        uuid = self.kwargs.get(self.lookup_field)

        with get_zaaktypen_client(self.zgw_group.ztc_service) as client:
            return client.get_item_by_uuid(uuid)

    def get_queryset(self, params: dict) -> list[ZaakTypeAPI] | None:
        """
        Retrieve all Zaaktypen available for the configured service.

        This method is overridden because no Django model queryset exists.
        ZaakType data is retrieved dynamically from the external Zaaktypen
        API via the configured client.
        """

        query_params = params.copy()
        if query_params:
            if (keys := set(query_params.keys())) != {QUERY_PARAM_FIELD}:
                raise ValidationError(
                    _(
                        "Unexpected parameters: {keys}. Only '{query_key}' is allowed."
                    ).format(keys=", ".join(keys), query_key=QUERY_PARAM_FIELD),
                    code="unknown-parameters",
                )

            query_params[self.search_field] = query_params.pop(QUERY_PARAM_FIELD)

        with get_zaaktypen_client(self.zgw_group.ztc_service) as client:
            return client.get_cached_items(self.service.slug, query_params)


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                name="service_slug",
                type=str,
                location=OpenApiParameter.PATH,
                required=True,
            ),
            OpenApiParameter(
                name="zaaktypen_zaaktype_uuid",
                type=str,
                location=OpenApiParameter.PATH,
                required=True,
            ),
            OpenApiParameter(
                name=QUERY_PARAM_FIELD,
                description=_(
                    "A search term for the ZaakType service. "
                    "The search is performed against the `identificatie__icontains` field."
                ),
                required=False,
                location=OpenApiParameter.QUERY,
                type=str,
            ),
        ],
    ),
    retrieve=extend_schema(
        parameters=[
            OpenApiParameter(
                name="service_slug",
                type=str,
                location=OpenApiParameter.PATH,
                required=True,
            ),
            OpenApiParameter(
                name="zaaktypen_zaaktype_uuid",
                type=str,
                location=OpenApiParameter.PATH,
                required=True,
            ),
            OpenApiParameter(
                name="zaken_uuid",
                type=str,
                location=OpenApiParameter.PATH,
                required=True,
            ),
        ],
    ),
)
class ZaakViewSet(ReadOnlyViewSetMixin, viewsets.ViewSet):
    """
    Exposes Zaak from /services/<zgw-service>/zaaktypen/<zaaktype>/zaken
    """

    serializer_class = ZaakSerializer
    pagination_class = DynamicPageSizePagination
    lookup_field = "zaken_uuid"
    parent_lookup_field = "zaaktypen_zaaktype_uuid"
    search_field = "identificatie__icontains"
    queryset = None

    @property
    def zaaktype_url(self) -> str:
        zaaktype_uuid = self.kwargs.get(self.parent_lookup_field)

        with get_zaaktypen_client(self.zgw_group.ztc_service) as client:
            # TODO investigate here if you can use cache
            zaaktype = client.get_item_by_uuid(zaaktype_uuid)
            return zaaktype["url"]

    def get_object(self) -> ZaakTypeAPI | None:
        """
        Retrieve a single Zaak from the external service by UUID.

        This method is overridden because the ViewSet does not use a Django
        model or ORM queryset. Instead, the requested ZaakType is fetched
        directly from the external Zaken API using the client.
        """
        uuid = self.kwargs.get(self.lookup_field)
        with get_zaken_client(self.zgw_group.zrc_service) as client:
            return client.get_item_by_uuid(uuid)

    def get_queryset(self, params: dict) -> list[ZaakAPI] | None:
        """
        Retrieve all Zaken filtered by a specific Zaaktype.

        This method is overridden because no Django model queryset exists.
        Zaak data is retrieved dynamically from the external Zaken
        API via the configured client.
        """
        with get_zaken_client(self.zgw_group.zrc_service) as client:
            # TODO investigate here if you can use cache
            return client.get_items_by_zaaktype(self.zaaktype_url)
