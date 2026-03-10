from datetime import date
from typing import TypedDict
from uuid import UUID


class ZaakTypeAPI(TypedDict):
    uuid: UUID
    catalogus: str
    identificatie: str
    omschrijving: str
    beginGeldigheid: date | None
    eindeGeldigheid: date | None


class ZaakAPI(TypedDict):
    uuid: UUID
