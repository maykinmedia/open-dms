from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers


@extend_schema_serializer()
class DocumentSerializer(serializers.Serializer):
    uuid = serializers.CharField(help_text="Unieke resource identifier (UUID4)")
    url = serializers.URLField(
        help_text=_(
            "URL-referentie naar dit object. Dit is de unieke identificatie en locatie van dit object."
        ),
    )
    identificatie = serializers.CharField(
        help_text=_(
            "Een binnen een gegeven context ondubbelzinnige referentie "
            "naar het INFORMATIEOBJECT."
        )
    )
    bronorganisatie = serializers.CharField(
        help_text=_(
            "Het RSIN van de Niet-natuurlijk persoon zijnde de "
            "organisatie die het informatieobject heeft gecreëerd of "
            "heeft ontvangen en als eerste in een samenwerkingsketen "
            "heeft vastgelegd."
        )
    )
    creatiedatum = serializers.DateField(
        help_text=(
            "Een datum of een gebeurtenis in de levenscyclus van het INFORMATIEOBJECT."
        )
    )
    titel = serializers.CharField(
        help_text=_("De naam waaronder het INFORMATIEOBJECT formeel bekend is.")
    )
    auteur = serializers.CharField(
        help_text=_(
            "De persoon of organisatie die dit informatie object heeft aangemaakt"
        )
    )
    taal = serializers.CharField(
        help_text=_(
            "Een ISO 639-2/B taalcode waarin de inhoud van het "
            "INFORMATIEOBJECT is vastgelegd. Voorbeeld: `dut`. Zie: "
            "https://www.iso.org/standard/4767.html"
        ),
    )
    begin_registratie = serializers.DateTimeField(
        help_text=_(
            "Een datumtijd in ISO8601 formaat waarop deze versie van het INFORMATIEOBJECT is aangemaakt of gewijzigd."
        )
    )
    informatieobjecttype = serializers.CharField(
        help_text=_(
            "URL-referentie naar het INFORMATIEOBJECTTYPE (in de Catalogi API)."
        )
    )
    vertrouwelijkheidaanduiding = serializers.CharField(
        required=False,
        allow_null=True,
        help_text=_(
            "Aanduiding van de mate waarin het INFORMATIEOBJECT voor de openbaarheid bestemd is."
        ),
    )
    status = serializers.CharField(
        required=False,
        allow_null=True,
        help_text=_("Aanduiding van de stand van zaken van een INFORMATIEOBJECT. "),
    )
    formaat = serializers.CharField(
        required=False,
        allow_null=True,
        help_text=_(
            'Het "Media Type" (voorheen "MIME type") voor de wijze waarop'
            "de inhoud van het INFORMATIEOBJECT is vastgelegd in een "
            "computerbestand. Voorbeeld: `application/msword`. Zie: "
            "https://www.iana.org/assignments/media-types/media-types.xhtml"
        ),
    )
    bestandsnaam = serializers.CharField(
        required=False,
        allow_null=True,
        help_text=_(
            "De naam van het fysieke bestand waarin de inhoud van het "
            "informatieobject is vastgelegd, inclusief extensie."
        ),
    )
    link = serializers.URLField(
        required=False,
        allow_null=True,
        help_text="De URL waarmee de inhoud van het INFORMATIEOBJECT op te vragen is.",
    )
    beschrijving = serializers.CharField(
        required=False,
        allow_null=True,
        help_text=_(
            "Een generieke beschrijving van de inhoud van het INFORMATIEOBJECT."
        ),
    )
    verschijningsvorm = serializers.CharField(
        required=False,
        allow_null=True,
        help_text=_("De essentiële opmaakaspecten van een INFORMATIEOBJECT."),
    )
    bestandsomvang = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text=_("Aantal bytes dat de inhoud van INFORMATIEOBJECT in beslag neemt."),
    )
    inhoud = serializers.CharField(
        required=False,
        default="",
        help_text=_(
            "De inhoud van het INFORMATIEOBJECT, indien deze is opgenomen in de index."
        ),
    )
