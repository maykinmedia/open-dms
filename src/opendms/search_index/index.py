from datetime import date, datetime
from typing import TYPE_CHECKING

from elasticsearch.dsl import (
    Date,
    Document as ES_Document,
    InnerDoc,
    Keyword,
    M,
    Mapping,
    Nested,
    Object,
    Text,
    mapped_field,
)

from .typing import (
    IndexName,
)


class DocumentData(InnerDoc):
    attachment = Object(properties={"content": Text(analyzer="dutch")})


# create empty base mapping instance
DOCUMENT_MAPPING = Mapping()
# add the document_data to the mapping without adding it to the `Document` class.
DOCUMENT_MAPPING.field("document_data", Nested(DocumentData)._mapping.to_dict())


class Document(ES_Document):
    # See https://elasticsearch-dsl.readthedocs.io/en/latest/persistence.html#python-type-hints
    # for typing support.
    uuid: M[str] = mapped_field(Keyword(required=True))
    url: M[str] = mapped_field(Keyword(required=True))
    identificatie: M[str] = mapped_field(Keyword(required=True))
    bronorganisatie: M[str] = mapped_field(Keyword(required=True))

    titel: M[str] = mapped_field(Text(analyzer="dutch", required=True))
    beschrijving: M[str | None] = mapped_field(Text(analyzer="dutch"))
    auteur: M[str] = mapped_field(Text(analyzer="dutch"))
    taal: M[str] = mapped_field(Text(analyzer="dutch"))

    vertrouwelijkheidaanduiding: M[str | None] = mapped_field(Text(analyzer="dutch"))
    status: M[str | None] = mapped_field(Text(analyzer="dutch"))
    formaat: M[str | None] = mapped_field(Text(analyzer="dutch"))
    bestandsnaam: M[str | None] = mapped_field(Text(analyzer="dutch"))
    informatieobjecttype: M[str] = mapped_field(Text(analyzer="dutch"))
    verschijningsvorm: M[str | None] = mapped_field(Text(analyzer="dutch"))

    link: M[str | None] = mapped_field(Text(analyzer="dutch"))

    creatiedatum: M[date] = mapped_field(Date(format="yyyy-MM-dd"))
    ontvangstdatum: M[date | None] = mapped_field(Date(format="yyyy-MM-dd"))
    verzenddatum: M[date | None] = mapped_field(Date(format="yyyy-MM-dd"))
    begin_registratie: M[datetime] = mapped_field(Date())

    if TYPE_CHECKING:
        # help the type checkers a little bit
        _id: str

    class Meta:
        mapping = DOCUMENT_MAPPING

    class Index:
        name: IndexName = "document"
