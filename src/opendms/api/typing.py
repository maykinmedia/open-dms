from datetime import date
from typing import TypedDict
from uuid import UUID


class ZaakTypeAPI(TypedDict):
    uuid: UUID
    url: str
    catalogus: str
    identificatie: str
    omschrijving: str
    beginGeldigheid: date | None
    eindeGeldigheid: date | None


class ZaakAPI(TypedDict):
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
