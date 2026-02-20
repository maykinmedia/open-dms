from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers

from ...typing import DocumentIndexType


@extend_schema_serializer()
class DocumentSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    url = serializers.URLField()
    identificatie = serializers.CharField()
    bronorganisatie = serializers.CharField()
    creatiedatum = serializers.DateField()
    titel = serializers.CharField()
    auteur = serializers.CharField()
    taal = serializers.CharField()
    begin_registratie = serializers.DateTimeField()
    informatieobjecttype = serializers.CharField()
    vertrouwelijkheidaanduiding = serializers.CharField(required=False, allow_null=True)
    status = serializers.CharField(required=False, allow_null=True)
    formaat = serializers.CharField(required=False, allow_null=True)
    bestandsnaam = serializers.CharField(required=False, allow_null=True)
    link = serializers.URLField(required=False, allow_null=True)
    beschrijving = serializers.CharField(required=False, allow_null=True)
    ontvangstdatum = serializers.DateField(required=False, allow_null=True)
    verzenddatum = serializers.DateField(required=False, allow_null=True)
    verschijningsvorm = serializers.CharField(required=False, allow_null=True)
    bestandsomvang = serializers.IntegerField(required=False, allow_null=True)
    inhoud = serializers.CharField(required=False, default="")


class DocumentIndexSerializer(DocumentSerializer):
    # Optional fields for indexing content
    inhoud = serializers.URLField(
        required=False, allow_blank=True, default="", write_only=True
    )
    bestandsomvang = serializers.IntegerField(
        required=False, allow_null=True, default=None, write_only=True
    )

    def validate(self, attrs: DocumentIndexType):
        inhoud = attrs.get("inhoud")
        bestandsomvang = attrs.get("bestandsomvang")

        # Ensure bestandsomvang is provided when inhoud is present
        if inhoud and bestandsomvang is None:
            raise serializers.ValidationError(
                {"bestandsomvang": _("Field is required when using `inhoud`.")}
            )

        # Default `inhoud` to empty string if missing
        if "inhoud" not in attrs or attrs["inhoud"] is None:
            attrs["inhoud"] = ""

        return attrs
