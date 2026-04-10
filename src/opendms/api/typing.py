from datetime import date, datetime
from typing import Literal, TypedDict
from uuid import UUID


class PaginatedResponse[T](TypedDict):
    count: int
    results: list[T]


class ZaakType(TypedDict):
    uuid: UUID
    url: str
    catalogus: str
    identificatie: str
    omschrijving: str
    beginGeldigheid: date | None
    eindeGeldigheid: date | None


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


class ESZaak(TypedDict):
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
    service_slug: str | None
    group_slug: str | None


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

    zaak_referenties: list[Zaak]


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


ZaakTypenPaginatedResponse = PaginatedResponse[ZaakType]
ZakenPaginatedResponse = PaginatedResponse[Zaak]
DocumentsPaginatedResponse = PaginatedResponse[DocumentType]
ESDocumentsPaginatedResponse = PaginatedResponse[ESDocumentType]
