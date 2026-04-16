from typing import Literal

from django.utils.translation import gettext_lazy as _

from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.openapi import AutoSchema as _AutoSchema
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from rest_framework import serializers
from rest_framework.renderers import BaseRenderer
from vng_api_common.constants import VERSION_HEADER

QUERY_PARAM_FIELD = "search"

# Openapi query parameters
SERVICE_PARAM = OpenApiParameter(
    name="service_slug",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.PATH,
    required=True,
)
QUERY_PARAM = OpenApiParameter(
    name=QUERY_PARAM_FIELD,
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    description=_(
        "A search term for the ZaakType service. The search is performed "
        "against the `identificatie__icontains` field."
    ),
    required=False,
)
ZAAKTYPE_PARAM = OpenApiParameter(
    name="zaaktype_uuid",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.PATH,
    required=True,
)
ZAAK_PARAM = OpenApiParameter(
    name="zaak_uuid",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.PATH,
    required=True,
)
DOCUMENT_PARAM = OpenApiParameter(
    name="document_uuid",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.PATH,
    required=True,
)
ZAAKTYPEN_ZAAKTYPE_UUID_PARAM = OpenApiParameter(
    name="zaaktypen_zaaktype_uuid",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.PATH,
    required=True,
)
ZAKEN_ZAAK_UUID_PARAM = OpenApiParameter(
    name="zaken_zaak_uuid",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.PATH,
    required=True,
)

OpenApiTypeLiteral = Literal[
    OpenApiTypes.STR,
    OpenApiTypes.INT,
    OpenApiTypes.NUMBER,
    OpenApiTypes.BOOL,
    OpenApiTypes.UUID,
    OpenApiTypes.DATE,
    OpenApiTypes.DATETIME,
]


def param(
    name: str,
    description: str | None = None,
    type_param: OpenApiTypeLiteral = OpenApiTypes.STR,
    location: str = OpenApiParameter.QUERY,
    required: bool = False,
) -> OpenApiParameter:

    return OpenApiParameter(
        name=name,
        type=type_param,
        description=description,
        location=location,
        required=required,
    )


class AutoSchema(_AutoSchema):
    def get_response_serializers(
        self,
    ):
        if self.method == "DELETE":
            return {204: None}

        return super().get_response_serializers()

    def get_override_parameters(self):
        """Add version headers to responses"""
        params = super().get_override_parameters()
        version_headers = self.get_version_headers()

        return params + version_headers

    def get_version_headers(self) -> list[OpenApiParameter]:
        return [
            OpenApiParameter(
                name=VERSION_HEADER,
                type=str,
                location=OpenApiParameter.HEADER,
                description=_(
                    "Geeft een specifieke API-versie aan in de context van "
                    "een specifieke aanroep. Voorbeeld: 1.2.1."
                ),
                response=True,
            )
        ]

    def _map_serializer_field(self, field, direction, *args, **kwargs):
        schema = super()._map_serializer_field(field, direction, *args, **kwargs)

        if isinstance(field, serializers.JSONField):
            schema["type"] = "object"

        return schema


class AnonCSRFSessionAuthenticationExtension(OpenApiAuthenticationExtension):
    target_class = "opendms.accounts.api.authentication.AnonCSRFSessionAuthentication"
    name = "AnonCSRFSession"

    def get_security_definition(self, auto_schema):
        return {
            "type": "apiKey",
            "in": "header",
            "name": "X-CSRFToken",
        }


class PlainTextRenderer(BaseRenderer):
    media_type = "text/plain"
    format = "txt"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data.encode("utf-8") if isinstance(data, str) else data
