from typing import TYPE_CHECKING

from django.contrib.auth import login
from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import status
from rest_framework.generics import RetrieveAPIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .authentication import AnonCSRFSessionAuthentication
from .serializers import AuthSerializer, WhoAmISerializer
from ...utils.serializers import NonFieldErrorsSerializer

if TYPE_CHECKING:
    from django.contrib.auth.models import AnonymousUser

    from opendms.accounts.models import User

@extend_schema(
    tags=["accounts"],
    summary=_("login"),
    description=_("Authenticates the user, returns user details on successful login."),
    responses={
        200: WhoAmISerializer,
        400: OpenApiResponse(
            response=NonFieldErrorsSerializer,
            description="Validation error"
        ),
    },
)
class LoginView(APIView):
    authentication_classes = (AnonCSRFSessionAuthentication,)
    permission_classes = ()
    serializer_class = AuthSerializer

    def post(self, request: Request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user: User = serializer.validated_data["user"]
        login(request._request, user)  # noqa - Access to a protected member _request of a class
        return Response(WhoAmISerializer(user).data, status=status.HTTP_200_OK)


@extend_schema(
    tags=["accounts"],
    summary=_("whoami"),
    description=_("Returns the current logged in user."),
    responses={
        200: WhoAmISerializer,
    },
)
class WhoAmIView(RetrieveAPIView):
    serializer_class = WhoAmISerializer
    permission_classes = []

    def get_object(self) -> User | AnonymousUser:
        return self.request.user
