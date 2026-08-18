import os
import re
import tempfile
from collections.abc import Mapping
from datetime import datetime
from time import sleep

from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import structlog
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from requests import HTTPError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from zgw_consumers.constants import APITypes
from zgw_consumers.models import Service

from opendms.doc_edit.backends.ms_graph_api.backend import MsGraphApiBackend
from opendms.doc_edit.models import BaseDriveDocument
from opendms.search_index.client import get_elasticsearch_client

from ..doc_edit.utils import is_within_threshold
from .clients import (
    get_documenten_client,
    get_informatieobjecttypen_client,
    get_statustypen_client,
    get_zaaktypen_client,
    get_zaken_client,
)
from .models import ZGWApiGroupConfig
from .serializers import (
    DocumentCreateSerializer,
    DocumentSerializer,
    InformatieObjectTypeSerializer,
    SearchResponseSerializer,
    SearchSerializer,
    ServiceSerializer,
    StatusTypeSerializer,
    ZaakCreateSerializer,
    ZaakInformatieObjectCreateSerializer,
    ZaakSerializer,
    ZaakTypeSerializer,
)
from .typing import (
    DocumentsPaginatedResponse,
    DocumentType,
    InformatieObjectType,
    InformatieObjectTypenPaginatedResponse,
    PaginatedResponse,
    SearchParameters,
    StatusType,
    Zaak,
    ZaakType,
    ZaakTypenPaginatedResponse,
)
from .utils.mixins import ReadOnlyViewSetMixin
from .utils.pagination import CountedPagination
from .utils.schema import (
    DOCUMENT_PARAM,
    QUERY_PARAM,
    QUERY_PARAM_FIELD,
    SERVICE_PARAM,
    STATUSTYPE_PARAM,
    ZAAK_PARAM,
    ZAAKTYPE_PARAM,
    ZAAKTYPEN_ZAAKTYPE_UUID_PARAM,
    ZAKEN_ZAAK_UUID_PARAM,
    PlainTextRenderer,
    param,
)

logger = structlog.stdlib.get_logger(__name__)

document_edit_backend = MsGraphApiBackend()


class WebhookView(APIView):
    renderer_classes = [PlainTextRenderer]
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Webhook callback",
        description="Endpoint webhook che riceve notifiche dal backend document_edit.",
        request=OpenApiTypes.OBJECT,
        responses={
            (status.HTTP_200_OK, "text/plain"): OpenApiResponse(
                description="Webhook verwerkt",
                response=OpenApiTypes.STR,
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Ongeldige payload",
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        return document_edit_backend.updated_callback(request)


class MsAuthCallbackView(APIView):
    @extend_schema(
        summary="Microsoft authentication callback",
        description="Callback endpoint voor Microsoft OAuth authenticatie.",
        responses={
            status.HTTP_302_FOUND: OpenApiResponse(
                description="Redirect naar de oorspronkelijke URL na succesvolle authenticatie",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Invalid callback of fout tijdens authenticatie",
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="Authenticatie mislukt (geen access token)",
            ),
        },
    )
    def get(self, request, *args, **kwargs):
        try:
            # Process callback
            document_edit_backend.authenticated_callback(request)

            # Redirect to "origin_url"
            origin_url = request.session.pop("origin_url", "/")
            return redirect(origin_url)
        except PermissionError as exc:
            # When the authentication fails
            logger.exception(str(exc))
            return Response(
                {"status": "error", "detail": _("Authentication failed")},
                status=403,
            )
        except OSError as exc:
            # When the authentication initialization fails
            logger.exception(str(exc))
            return Response(
                {"status": "error", "detail": "Invalid callback"},
                status=400,
            )


class SearchView(APIView):
    # TODO make GET is not allowed
    # TODO check extend_schema
    @extend_schema(
        tags=["search"],
        summary=_("Search"),
        operation_id="search",
        description=_("Search the document records."),
        request=SearchSerializer,
        responses=SearchResponseSerializer,
    )
    def post(self, request, *args, **kwargs):
        query_serializer = SearchSerializer(data=request.data)
        query_serializer.is_valid(raise_exception=True)
        params: SearchParameters = query_serializer.validated_data

        with get_elasticsearch_client() as client:
            search_results = client.get_search_results(
                query=params["query"],
                creatiedatum_from=params.get("creatiedatum_vanaf"),
                creatiedatum_to=params.get("creatiedatum_tot_en_met"),
                page=params["page"],
                page_size=params["page_size"],
                sort=params["sort"],
            )

        return Response(
            {
                "count": search_results.total_count,
                "results": search_results.results,
            }
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
            param(
                name="einddatum__isnull",
                description=_("De datum waarop de uitvoering van de zaak afgerond is."),
                type_param=OpenApiTypes.BOOL,
            ),
        ],
    ),
    retrieve=extend_schema(
        summary="zakenRetrieve",
        parameters=[
            SERVICE_PARAM,
            ZAAKTYPEN_ZAAKTYPE_UUID_PARAM,
            ZAAK_PARAM,
        ],
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
    def zaaktype_url(self) -> str | None:
        zaaktype_uuid = self.kwargs.get(self.parent_lookup_field)

        if not zaaktype_uuid:
            return None

        if not self._zaaktype_url:
            with get_zaaktypen_client(self.zgw_group.ztc_service) as client:
                # TODO investigate here if you can use cache
                zaaktype = client.get_item_by_uuid(zaaktype_uuid)
                self._zaaktype_url = zaaktype["url"]

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

    def get_paginated_queryset(
        self, params: Mapping[str, object]
    ) -> PaginatedResponse[Zaak]:
        """
        Retrieve all Zaken filtered by a specific Zaaktype.

        This method is overridden because no Django model queryset exists.
        Zaak data is retrieved dynamically from the external Zaken
        API via the configured client.
        """
        with get_zaken_client(self.zgw_group.zrc_service) as client:
            # TODO investigate here if you can use cache
            zaaktype_url = self.zaaktype_url

            if zaaktype_url:
                return client.get_paginated_items_by_zaaktype(
                    zaaktype_url,
                    params,
                )

            return client.get_paginated_items(params)


class ServiceZaakViewSet(ZaakViewSet):
    parent_lookup_field = None

    @extend_schema(
        summary="serviceZakenList",
        parameters=[
            OpenApiParameter(
                name="service_slug",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                required=True,
            ),
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
                    "De unieke identificatie van de ZAAK "
                    "(bevat de identificatie de gegeven waarden "
                    "(hoofdletterongevoelig))",
                ),
            ),
            param(
                name="omschrijving",
                description=_(
                    "Een korte omschrijving van de ZAAK "
                    "(bevat de omschrijving de gegeven waarden "
                    "(hoofdletterongevoelig))"
                ),
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="serviceZakenRetrieve",
        parameters=[
            OpenApiParameter(
                name="service_slug",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                required=True,
            ),
            ZAAK_PARAM,
        ],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def get_paginated_queryset(
        self,
        params: Mapping[str, object],
    ) -> PaginatedResponse[Zaak]:
        with get_zaken_client(self.zgw_group.zrc_service) as client:
            return client.get_paginated_items(params)

    @extend_schema(
        summary="serviceZakenCreate",
        request=ZaakCreateSerializer,
        responses={201: ZaakSerializer},
        parameters=[
            OpenApiParameter(
                name="service_slug",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                required=True,
            ),
        ],
    )
    def create(
        self,
        request: Request,
        *args,
        **kwargs,
    ) -> Response:
        serializer = ZaakCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data.copy()

        data["startdatum"] = data["startdatum"].isoformat()

        data["verantwoordelijkeOrganisatie"] = data.pop("verantwoordelijke_organisatie")

        with get_zaken_client(self.zgw_group.zrc_service) as client:
            zaak = client.create_zaak(data)

        response_serializer = ZaakSerializer(zaak)

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    list=extend_schema(
        summary="statustypenList",
        parameters=[SERVICE_PARAM],
    ),
    retrieve=extend_schema(
        summary="statustypenRetrieve",
        parameters=[SERVICE_PARAM, STATUSTYPE_PARAM],
    ),
)
class StatusTypeViewSet(ReadOnlyViewSetMixin, viewsets.ViewSet):
    """Read-only endpoint voor STATUSTYPEn"""

    _service: Service | None = None
    _zgw_group: ZGWApiGroupConfig | None = None

    serializer_class = StatusTypeSerializer
    lookup_field = STATUSTYPE_PARAM.name
    queryset = None

    def get_object(self) -> StatusType:
        # no queryset, do a service GET
        uuid = self.kwargs.get(self.lookup_field)
        assert uuid
        with get_statustypen_client(self.zgw_group.ztc_service) as client:
            return client.get_item_by_uuid(uuid)

    def get_paginated_queryset(
        self, params: Mapping[str, object]
    ) -> PaginatedResponse[StatusType]:
        # not queryset, but a paginated Service response
        with get_statustypen_client(self.zgw_group.ztc_service) as client:
            return client.get_paginated_items(params)


@extend_schema_view(
    list=extend_schema(
        summary="statustypenList",
        parameters=[SERVICE_PARAM, ZAAKTYPEN_ZAAKTYPE_UUID_PARAM],
    ),
    retrieve=extend_schema(
        summary="statustypenRetrieve",
        parameters=[SERVICE_PARAM, ZAAKTYPEN_ZAAKTYPE_UUID_PARAM, STATUSTYPE_PARAM],
    ),
)
class StatusTypeListViewSet(StatusTypeViewSet):
    """Read-only endpoint voor alle STATUSTYPEn die mogelijk zijn voor een bepaald ZAAKTYPE."""

    _service: Service | None = None
    _zgw_group: ZGWApiGroupConfig | None = None
    _zaaktype_url: str | None = None

    serializer_class = StatusTypeSerializer
    pagination_class = CountedPagination
    parent_lookup_field = ZAAKTYPEN_ZAAKTYPE_UUID_PARAM.name
    lookup_field = STATUSTYPE_PARAM.name
    queryset = None

    @property
    def zaaktype_url(self) -> str:
        if not self._zaaktype_url:
            zaaktype_uuid = self.kwargs.get(self.parent_lookup_field)
            assert zaaktype_uuid
            with get_zaaktypen_client(self.zgw_group.ztc_service) as client:
                zaaktype = client.get_item_by_uuid(zaaktype_uuid)
                self._zaaktype_url = zaaktype["url"]
        return self._zaaktype_url

    def get_paginated_queryset(
        self, params: Mapping[str, object]
    ) -> PaginatedResponse[StatusType]:
        # not a queryset, but a paginated Service response
        with get_statustypen_client(self.zgw_group.ztc_service) as client:
            return client.get_paginated_items({"zaaktype": self.zaaktype_url, **params})


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
    _object = None

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
        if not self._object:
            uuid = self.kwargs.get(self.lookup_field)
            with get_documenten_client(self.zgw_group.drc_service) as client:
                self._object = client.get_item_by_uuid(uuid)
        return self._object

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
    def download(self, request: Request, *args, **kwargs):
        obj = self.get_object()
        with get_documenten_client(self.zgw_group.drc_service) as client:
            response = client.download_document(obj)
            return response

    @extend_schema(
        "document_edit",
        summary="documentsEdit",
        description=_("Een document met binaire gegevens bewerken op OneDrive"),
        parameters=[
            SERVICE_PARAM,
            ZAAKTYPEN_ZAAKTYPE_UUID_PARAM,
            ZAKEN_ZAAK_UUID_PARAM,
            DOCUMENT_PARAM,
            OpenApiParameter(
                name="originUrl",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description=_(
                    "URL to redirect to in case of a renewed authentication flow"
                ),
            ),
        ],
        # TOOD: Improve
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description=_("Editor URL as a body"),
            ),
            status.HTTP_403_FORBIDDEN: OpenApiResponse(
                description=_("Authentication URL as body"),
            ),
            status.HTTP_423_LOCKED: OpenApiResponse(
                description=_("Empty body, document is locked"),
            ),
        },
    )
    @action(methods=["get"], detail=True, name="document_edit")
    def edit(self, request: Request, *args, **kwargs):
        # Get document
        obj = self.get_object()
        if not obj:
            raise Http404

        # Download file contents
        with get_documenten_client(self.zgw_group.drc_service) as client:
            file_response = client.download_document(obj)

        # Get file meta-information
        file_ext = file_response.get("File-Extension", "")
        file_uuid = self.kwargs.get(self.lookup_field)
        tmp_path = None

        try:
            # Create the `tmp_file`
            with tempfile.NamedTemporaryFile(
                suffix=file_ext,
                delete=False,
            ) as tmp_file:
                tmp_file.write(file_response.content)
                tmp_path = tmp_file.name

            # Open `tmp_file` in document_edit_backend
            # This returns a response containing the editor URL as a body.
            # The frontend opens this URL in a new window.
            # Due to implementation-specific CORS restrictions, we can't reply with a `HttpResponseRedirect` and the target location is set on the
            #  body.
            return document_edit_backend.open(request, tmp_path, file_uuid, file_ext)
        except PermissionError:
            # Indicate an authentication failure to the frontend.
            # The returned `response.url` is used by the frontend to redirect the user through and authentication flow.
            # Due to implementation-specific CORS restrictions, we can't reply with a `HttpResponseRedirect` and the target location is set on the
            #  body.
            request.session["origin_url"] = request.GET.get("originUrl")
            response = document_edit_backend.authenticate(request)
            return HttpResponseForbidden(response.url)
        except BlockingIOError:
            return HttpResponse(status=status.HTTP_423_LOCKED)
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

    @extend_schema(
        "document_upload",
        summary="documentsUpload",
        description=_("Een nieuwe versie van een document uploaden naar OpenZaak"),
        parameters=[
            SERVICE_PARAM,
            ZAAKTYPEN_ZAAKTYPE_UUID_PARAM,
            ZAKEN_ZAAK_UUID_PARAM,
            DOCUMENT_PARAM,
        ],
    )
    @action(methods=["get"], detail=True, name="document_upload")
    def upload(self, request: Request, *args, **kwargs):
        """
        Updates the document back to Open Zaak by downloading the file from OneDrive and uploading it to Open Zaak.

        TODO: What about versions/publishing?

        FIXME: DATA HAZARD
        FIXME: OneDrive may fall behind
        FIXME:
        FIXME: Due to the fact that One Drive may fall behind, this implements change detection based on unguaranteed
        FIXME: presence of the version in the "eTag", with an inaccurate "lastModifiedDateTime" check as fallback.
        FIXME:
        FIXME: Currently not guaranteed the last version is correctly uploaded.

        FIXME: This implements the ineternals of the OneDrive backend directly instead of relying on the public
        FIXME: interface
        """

        # Step 1: Get the access token for future requests.
        access_token = request.session.get("access_token", None)
        if not access_token:
            return self._redirect_to_ms_auth(request)

        document_edit_backend._set_token(access_token)

        # Step 2: Get the BaseDriveDocument.
        document_uuid = self.kwargs.get(self.lookup_field)
        document = BaseDriveDocument.objects.filter(document_uuid=document_uuid).first()

        if not document:
            return Response(
                "Document not found in OneDrive", status=status.HTTP_404_NOT_FOUND
            )

        # Step 3: Naive attempt to check if the resolved version on OneDrive is up2date (eventual consistency here).
        # Each round is delayed by a second, this may be a slow call.
        #
        # We check based on:
        # - eTag version
        # - lastModifiedDateTime

        retry = True
        attempts = 0
        max_retries = 10

        while retry:
            attempts = attempts + 1

            drive_item_info = document_edit_backend.one_drive_client.get_item_info(
                item_id=document.document_drive_id
            )

            last_modified_str = drive_item_info["lastModifiedDateTime"]
            last_modified = datetime.fromisoformat(
                last_modified_str.replace("Z", "+00:00")
            )

            etag_str = drive_item_info["eTag"]
            document_version = (
                self._extract_version_from_etag(document.etag)
                if document.etag
                else None
            )
            onedrive_version = (
                self._extract_version_from_etag(etag_str) if etag_str else None
            )

            if document_version is not None and onedrive_version is not None:
                # OneDrive has a newer version, continue
                if onedrive_version > document_version:
                    retry = False

                # OneDrive has an older or equal version, retry?
                if onedrive_version <= document_version:
                    retry = True

            if document_version is None or onedrive_version is None:
                # Actually, the fallback, version is not detected, is "lastModifiedDateTime" newer?
                if last_modified >= document.updated_at or is_within_threshold(
                    last_modified, document.updated_at
                ):
                    retry = False

            # Timeout
            if attempts >= max_retries:
                retry = False

            sleep(1)

        # After polling, we're still going to do another round to allow the data to be persisted on content level.
        sleep(3)  # ¯\_(ツ)_/¯

        file_response = document_edit_backend.one_drive_client._request(
            "GET", drive_item_info["@microsoft.graph.downloadUrl"], raw_response=True
        )
        drive_item_info = document_edit_backend.one_drive_client.get_item_info(
            item_id=document.document_drive_id
        )

        with get_documenten_client(self.zgw_group.drc_service) as client:
            status_code, message = client.upload_document(
                document_uuid,
                content=file_response.content,
                size=drive_item_info["size"],
                mime_type=drive_item_info["file"]["mimeType"],
            )

        # Mark as up-to-date
        document.etag = drive_item_info["eTag"]
        document.synced_at = document.updated_at
        document.save()

        return Response(message, status=status_code)

    @extend_schema(
        summary="documentsCreate",
        request=DocumentCreateSerializer,
        responses={201: DocumentSerializer},
        parameters=[
            SERVICE_PARAM,
            ZAAKTYPEN_ZAAKTYPE_UUID_PARAM,
            ZAKEN_ZAAK_UUID_PARAM,
        ],
    )
    def create(self, request, *args, **kwargs):
        serializer = DocumentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with get_documenten_client(self.zgw_group.drc_service) as client:
            document = client.create_document(serializer.validated_data)

        return Response(
            DocumentSerializer(document).data,
            status=status.HTTP_201_CREATED,
        )

    def _extract_version_from_etag(self, etag: str):
        """
        "{A51EDD09-8271-4C43-A73C-DB11808626A1},157" -> 157
        """
        version_str = re.search(r"(?:,)(\d+)", etag).group(1)
        version = int(version_str) if version_str else None
        return version

    def _redirect_to_ms_auth(self, request: Request):
        callback_url = request.build_absolute_uri(reverse("ms_auth_callback"))
        request.session["origin_url"] = request.build_absolute_uri()
        return document_edit_backend.authenticate(request, redirect_url=callback_url)


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                name="service_slug",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                required=True,
            ),
        ],
    ),
    retrieve=extend_schema(
        parameters=[
            OpenApiParameter(
                name="service_slug",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                required=True,
            ),
            OpenApiParameter(
                name="informatieobjecttype_uuid",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                required=True,
            ),
        ],
    ),
)
class InformatieObjectTypeViewSet(
    ReadOnlyViewSetMixin,
    viewsets.ViewSet,
):
    serializer_class = InformatieObjectTypeSerializer
    lookup_url_kwarg = "informatieobjecttype_uuid"

    def get_paginated_queryset(
        self,
        params: dict,
    ) -> InformatieObjectTypenPaginatedResponse:
        with get_informatieobjecttypen_client(self.service) as client:
            return client.get_paginated_items(params)

    def get_object(self) -> InformatieObjectType:
        uuid = self.kwargs[self.lookup_url_kwarg]

        with get_informatieobjecttypen_client(self.service) as client:
            return client.get_item_by_uuid(uuid)


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                name="service_slug",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                required=True,
            ),
        ]
    ),
    retrieve=extend_schema(
        parameters=[
            OpenApiParameter(
                name="service_slug",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                required=True,
            ),
            OpenApiParameter(
                name="id",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                required=True,
            ),
        ],
    ),
)
class ServiceZaakInformatieObjectViewSet(
    ReadOnlyViewSetMixin,
    viewsets.ViewSet,
):
    serializer_class = ZaakInformatieObjectCreateSerializer
    pagination_class = CountedPagination
    queryset = None
    lookup_field = "pk"

    def get_paginated_queryset(self, params):
        with get_zaken_client(self.zgw_group.zrc_service) as client:
            return client.get_paginated_zaakinformatieobjecten(params)

    def get_object(self):
        uuid = self.kwargs[self.lookup_field]

        with get_zaken_client(self.zgw_group.zrc_service) as client:
            return client.get_zaakinformatieobject(uuid)

    @extend_schema(
        summary="zaakinformatieobjectCreate",
        parameters=[
            OpenApiParameter(
                name="service_slug",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                required=True,
            ),
        ],
        request=ZaakInformatieObjectCreateSerializer,
        responses={201: OpenApiTypes.OBJECT},
    )
    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            with get_zaken_client(self.zgw_group.zrc_service) as client:
                result = client.create_zaakinformatieobject(serializer.validated_data)
        except HTTPError as exc:
            return Response(
                exc.response.json(),
                status=exc.response.status_code,
            )

        return Response(
            result,
            status=status.HTTP_201_CREATED,
        )
