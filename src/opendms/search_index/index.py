import os
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import TYPE_CHECKING

from elasticsearch.dsl import (
    Date,
    Document as ES_Document,
    InnerDoc,
    Keyword,
    Long,
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

CHECK_EXTENSION_DAYS = 10

DEFAULT_ANALYZER = os.environ.get("ELASTICSEARCH_ANALYZER", "dutch")


class DocumentData(InnerDoc):
    attachment = Object(properties={"content": Text(analyzer=DEFAULT_ANALYZER)})


class ZaakReferenties(InnerDoc):
    uuid: M[str] = mapped_field(Keyword(required=True))
    url: M[str] = mapped_field(Keyword(required=True))
    identificatie: M[str] = mapped_field(Keyword(required=True))
    bronorganisatie: M[str] = mapped_field(Keyword(required=True))
    verantwoordelijkeOrganisatie: M[str] = mapped_field(Keyword(required=True))
    omschrijving: M[str | None] = mapped_field(Text(analyzer=DEFAULT_ANALYZER))
    toelichting: M[str | None] = mapped_field(Text(analyzer=DEFAULT_ANALYZER))
    status: M[str | None] = mapped_field(Text(analyzer=DEFAULT_ANALYZER))
    registratiedatum: M[date] = mapped_field(Date(format="yyyy-MM-dd"))
    startdatum: M[date] = mapped_field(Date(format="yyyy-MM-dd"))
    zaaktype: M[str] = mapped_field(Keyword(required=True))
    object_type: M[str] = mapped_field(Keyword(required=True))

    service_slug: M[str | None] = mapped_field(Keyword())


# create empty base mapping instance
DOCUMENT_MAPPING = Mapping()
# add the document_data to the mapping without adding it to the `Document` class.
DOCUMENT_MAPPING.field("document_data", Nested(DocumentData)._mapping.to_dict())
DOCUMENT_MAPPING.field("zaak_referenties", Nested(ZaakReferenties)._mapping.to_dict())


class Document(ES_Document):
    # See https://elasticsearch-dsl.readthedocs.io/en/latest/persistence.html#python-type-hints
    # for typing support.
    uuid: M[str] = mapped_field(Keyword(required=True))
    url: M[str] = mapped_field(Keyword(required=True))
    identificatie: M[str] = mapped_field(Keyword(required=True))
    bronorganisatie: M[str] = mapped_field(Keyword(required=True))

    titel: M[str] = mapped_field(Text(analyzer=DEFAULT_ANALYZER, required=True))
    beschrijving: M[str | None] = mapped_field(Text(analyzer=DEFAULT_ANALYZER))
    auteur: M[str] = mapped_field(Text(analyzer=DEFAULT_ANALYZER))
    taal: M[str] = mapped_field(Text(analyzer=DEFAULT_ANALYZER))

    vertrouwelijkheidaanduiding: M[str | None] = mapped_field(
        Text(analyzer=DEFAULT_ANALYZER)
    )
    status: M[str | None] = mapped_field(Text(analyzer=DEFAULT_ANALYZER))
    formaat: M[str | None] = mapped_field(Text(analyzer=DEFAULT_ANALYZER))
    bestandsnaam: M[str | None] = mapped_field(Text(analyzer=DEFAULT_ANALYZER))
    informatieobjecttype: M[str] = mapped_field(Text(analyzer=DEFAULT_ANALYZER))
    verschijningsvorm: M[str | None] = mapped_field(Text(analyzer=DEFAULT_ANALYZER))

    link: M[str | None] = mapped_field(Text(analyzer=DEFAULT_ANALYZER))

    creatiedatum: M[date] = mapped_field(Date(format="yyyy-MM-dd"))
    begin_registratie: M[datetime] = mapped_field(Date())

    inhoud: M[str | None] = mapped_field(Text())
    bestandsomvang: M[int | None] = mapped_field(Long())

    zaak_referenties: M[list[ZaakReferenties]] = mapped_field(Nested(ZaakReferenties))

    last_checked_at: M[datetime] = mapped_field(Date())
    next_check_at: M[datetime] = mapped_field(Date())

    service_slug: M[str] = mapped_field(Keyword())
    group_slug: M[str | None] = mapped_field(Keyword())

    if TYPE_CHECKING:
        # help the type checkers a little bit
        _id: str

    class Meta:
        mapping = DOCUMENT_MAPPING

    class Index:
        name: IndexName = "document"

    def save(self, **kwargs):
        now = datetime.now(UTC)

        if not self.last_checked_at:
            self.last_checked_at = now

        if not self.next_check_at:
            self.next_check_at = now + timedelta(days=CHECK_EXTENSION_DAYS)

        return super().save(**kwargs)


class Zaak(ES_Document):
    uuid: M[str] = mapped_field(Keyword(required=True))
    url: M[str] = mapped_field(Keyword(required=True))
    identificatie: M[str] = mapped_field(Keyword(required=True))
    bronorganisatie: M[str] = mapped_field(Keyword(required=True))
    verantwoordelijkeOrganisatie: M[str] = mapped_field(Keyword(required=True))

    omschrijving: M[str | None] = mapped_field(Text(analyzer=DEFAULT_ANALYZER))
    toelichting: M[str | None] = mapped_field(Text(analyzer=DEFAULT_ANALYZER))
    status: M[str | None] = mapped_field(Text(analyzer=DEFAULT_ANALYZER))

    registratiedatum: M[date] = mapped_field(Date(format="yyyy-MM-dd"))
    startdatum: M[date] = mapped_field(Date(format="yyyy-MM-dd"))
    zaaktype: M[str] = mapped_field(Keyword(required=True))

    service_slug: M[str] = mapped_field(Keyword())
    group_slug: M[str | None] = mapped_field(Keyword())

    creatiedatum: M[date] = mapped_field(Date(format="yyyy-MM-dd"))

    class Index:
        name: IndexName = "zaak"

    def save(self, **kwargs):
        self.creatiedatum = self.registratiedatum
        return super().save(**kwargs)


@dataclass
class DocumentResults:
    total_count: int
    results: Sequence[Document]


@dataclass
class Results:
    total_count: int
    results: Sequence[Document | Zaak]
