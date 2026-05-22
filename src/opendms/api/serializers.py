from django.db.models import F, Q
from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import (
    PolymorphicProxySerializer,
    extend_schema_field,
    extend_schema_serializer,
)
from rest_framework import serializers
from zgw_consumers.models import Service

from ..doc_edit.models import BaseDriveDocument
from .constants import SortChoices
from .typing import ESDocumentType


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
    url = serializers.URLField(
        help_text=_(
            "URL-referentie naar dit object. Dit is de unieke identificatie en locatie van dit object."
        ),
    )
    catalogus = serializers.URLField(
        help_text=_("URL-referentie naar de CATALOGUS waartoe dit ZAAKTYPE behoort."),
    )
    concept = serializers.BooleanField(
        help_text=_(
            "Geeft aan of het object een concept betreft. Concepten zijn niet-definitieve versies en zouden niet gebruikt moeten worden buiten deze API."
        )
    )
    identificatie = serializers.CharField(
        help_text=_(
            "Unieke identificatie van het ZAAKTYPE binnen de CATALOGUS waarin het ZAAKTYPE voorkomt."
        ),
    )
    omschrijving = serializers.CharField(
        help_text=_("Omschrijving van de aard van ZAAKen van het ZAAKTYPE."),
    )
    versiedatum = serializers.DateField(
        help_text=_(
            "De datum waarop de (gewijzigde) kenmerken van het ZAAKTYPE geldig zijn geworden"
        )
    )
    beginGeldigheid = serializers.DateField(
        help_text=_("De datum waarop het is ontstaan."),
    )
    eindeGeldigheid = serializers.DateField(
        help_text=_("De datum waarop het is opgeheven."),
    )


class ZaakSerializer(serializers.Serializer):
    uuid = serializers.UUIDField(
        help_text=_(
            "UUID van dit object. Dit is de unieke identificatiecode van dit object."
        ),
    )
    url = serializers.URLField(
        help_text=_(
            "URL-referentie naar dit object. Dit is de unieke identificatie en locatie van dit object."
        ),
    )
    identificatie = serializers.CharField(
        help_text=_(
            "De unieke identificatie van de ZAAK binnen de organisatie "
            "die verantwoordelijk is voor de behandeling van de ZAAK.",
        ),
    )
    zaaktype = serializers.CharField(
        help_text=_("URL-referentie naar het ZAAKTYPE (in de Catalogi API)."),
    )
    bronorganisatie = serializers.CharField(
        help_text=_(
            "Het RSIN van de Niet-natuurlijk persoon zijnde de "
            "organisatie die de zaak heeft gecreeerd."
        ),
    )
    verantwoordelijkeOrganisatie = serializers.CharField(
        help_text=_(
            "Het RSIN van de Niet-natuurlijk persoon zijnde de organisatie "
            "die eindverantwoordelijk is voor de behandeling van de zaak."
        ),
    )
    registratiedatum = serializers.DateField(
        help_text=_(
            "De datum waarop de zaakbehandelende organisatie de ZAAK heeft geregistreerd"
        ),
    )
    startdatum = serializers.DateField(
        help_text=_("De datum waarop met de uitvoering van de zaak is gestart."),
    )
    omschrijving = serializers.CharField(
        help_text=_("Een korte omschrijving van de zaak."),
    )
    toelichting = serializers.CharField(
        help_text=_("Een toelichting op de zaak."),
    )


class ESZaakSerializer(serializers.Serializer):
    uuid = serializers.UUIDField(
        help_text=_(
            "UUID van dit object. Dit is de unieke identificatiecode van dit object."
        ),
    )
    url = serializers.URLField(
        help_text=_(
            "URL-referentie naar dit object. Dit is de unieke identificatie en locatie van dit object."
        ),
    )
    identificatie = serializers.CharField(
        help_text=_(
            "De unieke identificatie van de ZAAK binnen de organisatie "
            "die verantwoordelijk is voor de behandeling van de ZAAK.",
        ),
    )
    zaaktype = serializers.CharField(
        help_text=_("URL-referentie naar het ZAAKTYPE (in de Catalogi API)."),
    )
    bronorganisatie = serializers.CharField(
        help_text=_(
            "Het RSIN van de Niet-natuurlijk persoon zijnde de "
            "organisatie die de zaak heeft gecreeerd."
        ),
    )
    verantwoordelijkeOrganisatie = serializers.CharField(
        help_text=_(
            "Het RSIN van de Niet-natuurlijk persoon zijnde de organisatie "
            "die eindverantwoordelijk is voor de behandeling van de zaak."
        ),
    )
    registratiedatum = serializers.DateField(
        help_text=_(
            "De datum waarop de zaakbehandelende organisatie de ZAAK heeft geregistreerd"
        ),
    )
    startdatum = serializers.DateField(
        help_text=_("De datum waarop met de uitvoering van de zaak is gestart."),
    )
    omschrijving = serializers.CharField(
        help_text=_("Een korte omschrijving van de zaak."),
    )
    toelichting = serializers.CharField(
        help_text=_("Een toelichting op de zaak."),
    )
    service_slug = serializers.CharField(
        required=False,
        allow_null=True,
        help_text=_("De slug van de bronservice die deze zaak heeft geïndexeerd."),
    )
    group_slug = serializers.CharField(
        required=False,
        allow_null=True,
        help_text=_(
            "De slug van de groep waartoe de bronservice behoort die deze zaak heeft geïndexeerd."
        ),
    )
    ztc_service_slug = serializers.CharField(
        required=False,
        allow_null=True,
        help_text=_(
            "De slug van de ZTC service die gekoppeld is aan de bronservice die deze zaak heeft geïndexeerd."
        ),
    )
    ztc_uuid = serializers.CharField(
        required=False,
        allow_null=True,
        help_text=_(
            "De UUID van de zaak in de ZTC, indien deze bekend is en gekoppeld kan worden."
        ),
    )
    startjaar = serializers.CharField(
        required=False,
        allow_null=True,
        help_text=_(
            "Het jaar waarin de zaak is gestart. Dit veld is optioneel en kan worden gebruikt voor aanvullende filtering of sortering op jaarniveau."
        ),
    )


@extend_schema_serializer()
class DocumentSerializer(serializers.Serializer):
    uuid = serializers.CharField(
        help_text=_("Unieke resource identifier (UUID4)"),
    )
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
        help_text=_(
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
        help_text=_(
            "De URL waarmee de inhoud van het INFORMATIEOBJECT op te vragen is."
        ),
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

    has_pending_updates = serializers.SerializerMethodField()

    @extend_schema_field(serializers.BooleanField)
    def get_has_pending_updates(self, document: ESDocumentType) -> bool:
        uuid = document["uuid"]
        qs = BaseDriveDocument.objects.filter(document_uuid=uuid).filter(
            Q(synced_at__isnull=True) | Q(updated_at__gt=F("synced_at"))
        )

        return qs.exists()


class ESDocumentSerializer(serializers.Serializer):
    uuid = serializers.CharField(
        help_text=_("Unieke resource identifier (UUID4)"),
    )
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
        help_text=_(
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
        help_text=_(
            "De URL waarmee de inhoud van het INFORMATIEOBJECT op te vragen is."
        ),
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
    service_slug = serializers.CharField(
        required=False,
        allow_null=True,
        help_text=_("De slug van de bronservice die dit document heeft geïndexeerd."),
    )
    group_slug = serializers.CharField(
        required=False,
        allow_null=True,
        help_text=_(
            "De slug van de groep waartoe de bronservice behoort die dit document heeft geïndexeerd."
        ),
    )
    zaak_referenties = ESZaakSerializer(many=True, required=False, default=list)


class SearchSerializer(serializers.Serializer):
    query = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_(
            "Filtering records based on the provided search term. "
            "The search is performed across both Documents and Zaken index."
            "This search is applied to the following fields:\n\n"
            "**Documents:**\n"
            "- `identificatie`\n"
            "- `titel`\n"
            "- `bronorganisatie`\n"
            "- `beschrijving`\n"
            "- `document_data.attachment.content`\n\n"
            "- `zaak_referenties.identificatie`\n"
            "- `zaak_referenties.omschrijving`\n"
            "- `zaak_referenties.toelichting`\n"
            "- `zaak_referenties.status`\n\n"
            "**Zaken:**\n"
            "- `identificatie`\n"
            "- `omschrijving`\n"
            "- `toelichting`\n"
            "- `status`\n\n"
            "You can use double quotes for exact matches and `AND`/`OR` syntax for complex queries."
        ),
        default="",
    )
    page = serializers.IntegerField(default=1, help_text=_("Page number."))
    page_size = serializers.IntegerField(
        default=10, help_text=_("Number of results per page.")
    )
    sort = serializers.ChoiceField(
        choices=SortChoices.choices, default=SortChoices.relevance
    )
    creatiedatum_vanaf = serializers.DateField(
        required=False,
        allow_null=True,
        default=None,
        help_text=_("Filter documents created on or after this date."),
    )
    creatiedatum_tot_en_met = serializers.DateField(
        required=False,
        allow_null=True,
        default=None,
        help_text=_("Filter documents created on or before this date."),
    )


class SearchResultDocumentSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=["document"])
    data = ESDocumentSerializer()


class SearchResultZaakSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=["zaak"])
    data = ESZaakSerializer()


class SearchResponseSerializer(serializers.Serializer):
    count = serializers.IntegerField()

    results = PolymorphicProxySerializer(
        component_name="SearchResult",
        serializers={
            "document": SearchResultDocumentSerializer,
            "zaak": SearchResultZaakSerializer,
        },
        resource_type_field_name="type",
        many=True,
    )
