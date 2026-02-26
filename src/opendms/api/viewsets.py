from rest_framework import viewsets
from vng_api_common.pagination import DynamicPageSizePagination
from zgw_consumers.constants import APITypes
from zgw_consumers.models import Service

from .serializers import ServiceSerializer


class ServiceViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Service.objects.filter(api_type=APITypes.ztc)
    serializer_class = ServiceSerializer
    pagination_class = DynamicPageSizePagination
    lookup_field = "slug"
