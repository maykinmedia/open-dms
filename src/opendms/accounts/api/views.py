from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth import login, logout
from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.generics import RetrieveAPIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from ...api.serializers import ValidationErrorsSerializer
from .authentication import AnonCSRFSessionAuthentication
from .serializers import AuthSerializer, WhoAmISerializer

if TYPE_CHECKING:
    from django.contrib.auth.models import AnonymousUser

    from opendms.accounts.models import User


@extend_schema(
    tags=["accounts"],
    summary=_("login"),
    description=_(
        "Authenticates the user, returns whoami details on successful login."
    ),
    responses={
        200: WhoAmISerializer,
        400: OpenApiResponse(
            response=ValidationErrorsSerializer, description="Validation error"
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
    summary=_("logout"),
    description=_(
        "Remove the authenticated user's ID from the request and flush their session "
        "data."
    ),
)
class LogoutView(APIView):
    permission_classes = ()
    serializer_class = None

    def get(self, request: Request, *args, **kwargs) -> Response:
        logout(request._request)  # noqa - Access to a protected member _request of a class
        return Response(status=status.HTTP_204_NO_CONTENT)


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
