from django.contrib.auth.models import AnonymousUser
from rest_framework import serializers

from opendms.accounts.models import User


class UserSerializer(serializers.ModelSerializer):
  class Meta:
    model = User
    fields = ("pk", "username", "first_name", "last_name", "email")


class WhoAmISerializer(serializers.Serializer):
  is_authenticated = serializers.BooleanField()
  user = serializers.SerializerMethodField()

  def get_user(self, user: User | AnonymousUser) -> dict | None:
    if user.is_authenticated:
      return UserSerializer(user).data
    return None
