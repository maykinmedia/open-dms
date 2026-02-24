from rest_framework import viewsets
from vng_api_common.pagination import DynamicPageSizePagination
from zgw_consumers.models import Service

from .serializers import ServiceSerializer


class ServiceViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Service.objects.all()  # TODO add filter APITypes='zrc' ?
    serializer_class = ServiceSerializer
    pagination_class = DynamicPageSizePagination
    lookup_field = "slug"
