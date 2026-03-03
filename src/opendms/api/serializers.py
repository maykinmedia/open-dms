from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from zgw_consumers.models import Service


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = (
            "slug",
            "label",
        )


class ZaakTypeSerializer(serializers.Serializer):
    uuid = serializers.UUIDField(
        help_text=_(
            "UUID van dit object. Dit is de unieke identificatiecode van dit object."
        ),
    )
    catalogus = serializers.URLField(
        help_text=_("URL-referentie naar de CATALOGUS waartoe dit ZAAKTYPE behoort."),
    )
    identificatie = serializers.CharField(
        help_text=_(
            "Unieke identificatie van het ZAAKTYPE binnen de CATALOGUS waarin het ZAAKTYPE voorkomt."
        ),
    )
    omschrijving = serializers.CharField(
        help_text=_("Omschrijving van de aard van ZAAKen van het ZAAKTYPE."),
    )
    beginGeldigheid = serializers.DateField(
        help_text=_("De datum waarop het is ontstaan."),
    )
    eindeGeldigheid = serializers.DateField(
        help_text=_("De datum waarop het is opgeheven."),
    )
