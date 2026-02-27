from rest_framework import viewsets
from rest_framework.filters import SearchFilter
from vng_api_common.pagination import DynamicPageSizePagination
from zgw_consumers.constants import APITypes
from zgw_consumers.models import Service

from .serializers import ServiceSerializer


class ServiceViewSet(viewsets.ReadOnlyModelViewSet):
    filter_backends = (SearchFilter,)
    queryset = Service.objects.filter(api_type=APITypes.ztc)
    lookup_field = "slug"
    pagination_class = DynamicPageSizePagination
    serializer_class = ServiceSerializer

    search_fields = ["slug", "api_root", "label"]
