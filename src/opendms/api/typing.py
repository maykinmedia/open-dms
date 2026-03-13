from datetime import date
from typing import TypedDict
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


ZaakTypenPaginatedResponse = PaginatedResponse[ZaakType]
ZakenPaginatedResponse = PaginatedResponse[Zaak]
