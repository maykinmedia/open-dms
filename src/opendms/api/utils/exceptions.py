from rest_framework import status
from rest_framework.exceptions import APIException


class ExternalServiceUnavailable(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "External service unreachable"
    default_code = "service_unavailable"


class ZGWGroupConfigurationMissing(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "No ZGW Configuration Group found for the given ztc service"
    default_code = "zgw_group_missing"
