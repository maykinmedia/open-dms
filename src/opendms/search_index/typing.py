from datetime import date, datetime
from typing import Literal, TypedDict

type IndexName = Literal["document"]


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
    inhoud: str
    link: str | None
    beschrijving: str | None
    verschijningsvorm: str | None
    bestandsomvang: int | None


class SearchParameters(TypedDict):
    query: str
    page: int
    page_size: int
    sort: Literal["relevance", "chronological"]
    creatiedatum_vanaf: date | None
    creatiedatum_tot_en_met: date | None
