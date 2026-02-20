from datetime import date, datetime
from typing import Literal, NotRequired, TypedDict

type IndexName = Literal["document"]


class NestedPublisherType(TypedDict):
    uuid: str
    naam: str


class NestedInformationCategoryType(TypedDict):
    uuid: str
    naam: str


class NestedTopicType(TypedDict):
    uuid: str
    officiele_titel: str


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
    vertrouwelijkheidaanduiding: NotRequired[str | None]
    status: NotRequired[str | None]
    formaat: NotRequired[str | None]
    bestandsnaam: NotRequired[str | None]
    inhoud: NotRequired[str]
    link: NotRequired[str | None]
    beschrijving: NotRequired[str | None]
    ontvangstdatum: NotRequired[date | None]
    verzenddatum: NotRequired[date | None]
    verschijningsvorm: NotRequired[str | None]
    bestandsomvang: NotRequired[int | None]


class DocumentIndexType(DocumentType):
    inhoud: str
    bestandsomvang: int | None


class SearchParameters(TypedDict):
    query: str
    page: int
    page_size: int
    sort: Literal["relevance", "chronological"]
    creatiedatum_vanaf: date | None
    creatiedatum_tot_en_met: date | None
