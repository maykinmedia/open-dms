from collections.abc import Mapping, Sequence
from datetime import date, datetime
from typing import Literal, NotRequired, TypedDict
from uuid import UUID

type JSONValue = None | bool | int | float | str | Sequence[JSONValue] | JSONObject
type JSONObject = Mapping[str, JSONValue]


class PaginatedResponse[T](TypedDict):
    count: int
    results: list[T]


class ZaakType(TypedDict):
    uuid: UUID
    url: str
    catalogus: str
    concept: bool
    identificatie: str
    omschrijving: str
    versiedatum: str
    beginGeldigheid: date | None
    eindeGeldigheid: date | None


class Status(TypedDict):
    url: str  # self URL
    uuid: UUID
    zaak: str  # URL
    statustype: str  # URL
    datumStatusGezet: datetime
    statustoelichting: str
    indicatieLaatstGezetteStatus: bool
    gezetdoor: str | None  # URL
    zaakinformatieobjecten: list[str]  # list[URL]


class ZaakExpansion(TypedDict):
    status: NotRequired[Status]


class Zaak(TypedDict):
    uuid: UUID
    url: str
    identificatie: str
    zaaktype: str
    bronorganisatie: str
    verantwoordelijkeOrganisatie: str
    registratiedatum: date
    startdatum: date
    omschrijving: str
    toelichting: str
    _expand: NotRequired[ZaakExpansion]


class ESZaak(TypedDict):
    uuid: UUID
    url: str
    identificatie: str
    zaaktype: str
    bronorganisatie: str
    verantwoordelijkeOrganisatie: str
    registratiedatum: str  # date our ES code doesn't handle date
    startdatum: str  # date our ES code doesn't handle date
    omschrijving: str
    toelichting: str
    service_slug: NotRequired[str | None]  # ZGW Zaken API doesn't return this
    group_slug: NotRequired[str | None]  # ZGW Zaken API doesn't return this
    ztc_service_slug: NotRequired[str | None]  # ZGW Zaken API doesn't return this
    ztc_uuid: NotRequired[UUID | None]  # ZGW Zaken API doesn't return this
    startjaar: NotRequired[str | None]  # ZGW Zaken API doesn't return this


class DocumentType(TypedDict):
    uuid: str
    url: str
    identificatie: str
    bronorganisatie: str
    creatiedatum: date
    titel: str
    auteur: str
    taal: str
    begin_registratie: datetime
    informatieobjecttype: str
    vertrouwelijkheidaanduiding: str | None
    status: str | None
    formaat: str | None
    bestandsnaam: str | None
    inhoud: str | None
    link: str | None
    beschrijving: str | None
    verschijningsvorm: str | None
    bestandsomvang: int | None


class ESDocumentType(TypedDict):
    uuid: str
    url: str
    identificatie: str
    bronorganisatie: str
    creatiedatum: date
    titel: str
    auteur: str
    taal: str
    begin_registratie: datetime
    informatieobjecttype: str
    vertrouwelijkheidaanduiding: str | None
    status: str | None
    formaat: str | None
    bestandsnaam: str | None
    inhoud: str | None
    link: str | None
    beschrijving: str | None
    verschijningsvorm: str | None
    bestandsomvang: int | None
    service_slug: str | None
    group_slug: str | None

    zaak_referenties: list[ESZaak]


class ObjectInformatieObjectType(TypedDict):
    url: str
    informatieobject: str
    object: str
    objecttype: str


class SearchParameters(TypedDict):
    query: str
    page: int
    page_size: int
    sort: Literal["relevance", "chronological"]
    creatiedatum_vanaf: date | None
    creatiedatum_tot_en_met: date | None


class CheckListItem(TypedDict):
    itemnaam: str
    toelichting: str | None
    vraagstelling: str
    verplicht: bool


class StatusType(TypedDict):
    uuid: UUID
    url: str
    omschrijving: str
    omschrijvingGeneriek: str
    statustekst: str
    zaaktype: str
    catalogus: str
    zaaktypeIdentificatie: str
    volgnummer: int
    isEindstatus: bool
    informeren: bool
    doorlooptijd: str | None
    toelichting: str | None
    checklistitemStatustype: list[CheckListItem]
    eigenschappen: list[str | None]


class InformatieObjectType(TypedDict):
    uuid: UUID
    url: str
    catalogus: str
    omschrijving: str
    vertrouwelijkheidaanduiding: str
    beginGeldigheid: str | None
    eindeGeldigheid: str | None
    concept: bool
    informatieobjectcategorie: str
    zaaktypen: list[str]


ZaakTypenPaginatedResponse = PaginatedResponse[ZaakType]
DocumentsPaginatedResponse = PaginatedResponse[DocumentType]
ESDocumentsPaginatedResponse = PaginatedResponse[ESDocumentType]
InformatieObjectTypenPaginatedResponse = PaginatedResponse[InformatieObjectType]
