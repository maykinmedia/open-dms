from typing import TYPE_CHECKING

from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework.generics import RetrieveAPIView

from opendms.accounts.api.serializers import WhoAmISerializer

if TYPE_CHECKING:
  from django.contrib.auth.models import AnonymousUser
  from opendms.accounts.models import User

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
