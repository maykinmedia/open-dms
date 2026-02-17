from django.contrib.auth import authenticate
from django.contrib.auth.models import AnonymousUser
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from opendms.accounts.models import User


class AuthSerializer(serializers.Serializer):
    username = serializers.CharField(label=_("Username"), write_only=True)
    password = serializers.CharField(
        label=_("Password"),
        style={"input_type": "password"},
        trim_whitespace=False,
        write_only=True,
    )

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get("request"),
            username=attrs["username"],
            password=attrs["password"],
        )

        # The authenticate call simply returns None for is_active=False
        # users. (Assuming the default ModelBackend authentication
        # backend.)
        if not user:
            raise serializers.ValidationError(
                _("Unable to log in with provided credentials."), code="authorization"
            )

        attrs["user"] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("pk", "username", "first_name", "last_name", "email")


class WhoAmISerializer(serializers.Serializer):
    is_authenticated = serializers.BooleanField()
    user = serializers.SerializerMethodField()

    @extend_schema_field(UserSerializer)
    def get_user(self, user: User | AnonymousUser) -> dict | None:
        if user.is_authenticated:
            return UserSerializer(user).data
        return None
