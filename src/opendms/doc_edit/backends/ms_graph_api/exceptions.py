from rest_framework import status
from rest_framework.exceptions import APIException


class MsGraphApiBackendError(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Failed to execute Ms GraphApi backend Request"
    default_code = "ms_graphapi_backend_error"
