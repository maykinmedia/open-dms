from rest_framework import status
from rest_framework.exceptions import APIException


class NoServiceConfigured(RuntimeError):
    pass


class ExternalServiceUnavailable(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "External service unreachable"
    default_code = "service_unavailable"
