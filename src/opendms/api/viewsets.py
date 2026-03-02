from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from requests.exceptions import RequestException
from rest_framework import exceptions, viewsets
from rest_framework.filters import SearchFilter
from vng_api_common.pagination import DynamicPageSizePagination
from zgw_consumers.constants import APITypes
from zgw_consumers.models import Service

from .clients.zaaktypen import ZaakTypeAPI, get_zaaktypen_client
from .serializers import ServiceSerializer, ZaakTypeSerializer
from .utils.exceptions import ExternalServiceUnavailable
from .utils.mixins import ReadOnlyViewSetMixin


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
    Exposes Zaaktypen from a ZGW service.
    """

    _service: Service | None = None

    serializer_class = ZaakTypeSerializer
    pagination_class = DynamicPageSizePagination
    lookup_field = "zaaktype_uuid"
    queryset = None

    @property
    def service(self) -> Service:
        if self._service is None:
            service_slug = self.kwargs.get("service_slug")
            if not service_slug:
                raise exceptions.NotFound(_("Service slug missing"))

            self._service = get_object_or_404(Service, slug=service_slug)

        return self._service

    def get_object(self) -> ZaakTypeAPI:
        uuid = self.kwargs.get(self.lookup_field)
        try:
            with get_zaaktypen_client(self.service) as client:
                return client.get_item_by_uuid(uuid)
        except RequestException:
            raise exceptions.NotFound(
                _("ZaakType with UUID {uuid} not found").format(uuid=uuid)
            )

    def get_queryset(self) -> list[ZaakTypeAPI]:
        try:
            with get_zaaktypen_client(self.service) as client:
                return client.get_cached_items(self.service.slug)
        except RequestException as exc:
            raise ExternalServiceUnavailable(
                _("External service '{self.service.slug}' unreachable.").format(
                    service_slug=self.service.slug
                )
            ) from exc
