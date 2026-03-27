import re
from datetime import date, datetime
from typing import Literal, assert_never
from urllib.parse import urlsplit

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _

import structlog
from elasticsearch import Elasticsearch
from elasticsearch.dsl import Q, Search
from elasticsearch.exceptions import NotFoundError

from .constants import DOCUMENT_ATTACHMENT_PIPELINE_ID, DOCUMENT_INDEX, ZAAK_INDEX
from .index import Document, DocumentResults, Results, Zaak
from .utils import download_document

logger = structlog.get_logger(__name__)


class ElasticSearchClient:
    # TODO add check if index exists, if not create it
    index = DOCUMENT_INDEX
    zaak_index = ZAAK_INDEX

    def __init__(self):
        self._settings = settings.SEARCH_INDEX
        self._validate_settings()
        self._client = None

    def _validate_settings(self) -> None:
        if not self._settings["HOST"]:
            raise ImproperlyConfigured(_("ELASTICSEARCH_HOST is not configured"))

        if self._settings["USER"] and not self._settings["PASSWORD"]:
            raise ImproperlyConfigured(
                _("ELASTICSEARCH_PASSWORD is required when USER is set")
            )

    def _get_client(self) -> Elasticsearch:
        host = self._settings["HOST"]
        username = self._settings["USER"]
        password = self._settings["PASSWORD"]
        basic_auth = (username, password) if username else None

        # REQUESTS_CA_BUNDLE is set by self-certifi OR could be set at deployment time, acts
        # as default if no explicit CA is specified.
        ca_certs: str | None = self._settings["CA_CERTS"] or settings.REQUESTS_CA_BUNDLE

        # can't just fallback to ca_certs=None since it has special meaning
        extra = {}
        if ca_certs and urlsplit(host).scheme == "https":  # pragma: no cover
            extra["ca_certs"] = ca_certs

        return Elasticsearch(
            host,
            # TODO test this with token
            # -H "Authorization: ApiKey "${API_KEY}""
            basic_auth=basic_auth,
            timeout=self._settings["TIMEOUT"],
            **extra,
        )

    def _clean_str_query(self, query: str) -> str:
        """
        Make the query suitable for ``simple_query_string`` search.

        While the ``query_string`` supports ``AND`` and ``OR`` out of the box, the
        ``simple_query_string`` does not appear to do so and requires us to convert
        this into the proper boolean operators (``+`` and ``|``).
        """
        # Pattern matches either a quoted substring (including quotes) or non-quote parts.
        pattern = r'"[^"]*"|[^"]+'
        parts: list[str] = re.findall(pattern, query)

        processed_parts = []
        for part in parts:
            # If the part starts and ends with a quote, assume it's a quoted phrase and
            # leave it unchanged.
            if part.startswith('"') and part.endswith('"'):
                processed_parts.append(part)
            else:
                # Replace standalone AND/OR with +/| using word boundaries.
                part = re.sub(r"\bAND\b", "+", part)
                part = re.sub(r"\bOR\b", "|", part)
                processed_parts.append(part)

        return "".join(processed_parts)

    def __enter__(self) -> "ElasticSearchClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            self._client.close()
            self._client = None

    @property
    def client(self) -> Elasticsearch | None:
        if self._client is None:
            self._client = self._get_client()
        return self._client

    @property
    def can_connect(self) -> bool:
        return self.client.ping()

    def get_search_results(
        self,
        query: str,
        creatiedatum_from: date | None = None,
        creatiedatum_to: date | None = None,
        page: int = 1,
        page_size: int = 10,
        sort: Literal["relevance", "chronological"] = "relevance",
    ) -> Results:
        """
        Perform a search across both Document and Zaak indices.
        Returns mixed results (Document | Zaak).
        """

        search = Search(index=[Document.Index.name, Zaak.Index.name])

        if query:
            cleaned_query = self._clean_str_query(query)

            doc_query = Q(
                "simple_query_string",
                query=cleaned_query,
                fields=[
                    "identificatie^3",
                    "titel^2",
                    "bestandsnaam^1.5",
                    "beschrijving^1.2",
                    "document_data.attachment.content",
                ],
                flags="OR|AND|PHRASE|PRECEDENCE|WHITESPACE",
                default_operator="AND",
            )

            zaak_index_query = Q(
                "simple_query_string",
                query=cleaned_query,
                fields=[
                    "identificatie^3",
                    "omschrijving^2",
                    "toelichting^1.5",
                    "status^1.2",
                ],
                flags="OR|AND|PHRASE|PRECEDENCE|WHITESPACE",
                default_operator="AND",
            )

            nested_zaak_query = Q(
                "nested",
                path="zaak_referenties",
                query=Q(
                    "simple_query_string",
                    query=cleaned_query,
                    fields=[
                        "zaak_referenties.identificatie^3",
                        "zaak_referenties.omschrijving^2",
                        "zaak_referenties.toelichting^1.5",
                        "zaak_referenties.status^1.2",
                    ],
                    flags="OR|AND|PHRASE|PRECEDENCE|WHITESPACE",
                    default_operator="AND",
                ),
                ignore_unmapped=True,
            )

            search = search.query(
                Q(
                    "bool",
                    should=[
                        doc_query,
                        nested_zaak_query,
                        zaak_index_query,
                    ],
                    minimum_should_match=1,
                )
            )

        if creatiedatum_from or creatiedatum_to:
            search = search.filter(
                "range",
                creatiedatum={
                    **({"gte": creatiedatum_from} if creatiedatum_from else {}),
                    **({"lte": creatiedatum_to} if creatiedatum_to else {}),
                },
            )

        # now, add the boosting via decay function to favour recently added documents over
        # older ones. Docs:
        # https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-function-score-query.html#gauss-decay
        search.query = Q(  # pyright: ignore[reportAttributeAccessIssue]
            "function_score",
            query=search.query or Q("match_all"),
            functions=[
                {
                    "gauss": {
                        "creatiedatum": {
                            "origin": "now",
                            # after ~two weeks, the decay will be 0.5
                            "scale": "15d",
                            # only start appylying decay to documents older than a week
                            "offset": "7d",
                            "decay": 0.5,
                        }
                    }
                }
            ],
            score_mode="multiply",
        )

        # add ordering configuration. note that sorting on score defaults to DESC, see:
        # https://www.elastic.co/guide/en/elasticsearch/reference/current/sort-search-results.html#_sort_order
        match sort:
            case "relevance":
                search = search.sort("_score", "-creatiedatum")
            case "chronological":
                search = search.sort("-creatiedatum", "_score")
            case _:  # pragma: no cover
                assert_never(sort)

        # and paginate it
        page_from = page_size * (page - 1)
        search = search[page_from : page_from + page_size]

        search = search.using(self.client)
        response = search.execute()

        results: list[Document | Zaak] = []

        for hit in response.hits:
            data = hit.to_dict()
            if hit.meta.index == Document.Index.name:
                results.append({"type": "document", "data": data})
            elif hit.meta.index == Zaak.Index.name:
                results.append({"type": "zaak", "data": data})

        return Results(
            total_count=response.hits.total.value,  # pyright: ignore[reportAttributeAccessIssue]
            results=results,
        )

    def get_all_documents(self, page: int = 1, page_size: int = 10) -> DocumentResults:
        """
        Retrieve all documents from the index, paginated.
        """
        search = Search(index=self.index, doc_type=Document)

        page_from = page_size * (page - 1)
        search = search[page_from : page_from + page_size]
        search = search.query("match_all")
        search = search.using(self.client)
        response = search.execute()
        # process the results
        return DocumentResults(
            total_count=response.hits.total.value,  # pyright: ignore[reportAttributeAccessIssue]
            results=[hit for hit in response.hits],
        )

    def get_total_count(self, index: str, doc_type: type) -> int:
        """
        Count documents in the index
        """

        search = Search(index=index, doc_type=doc_type).using(self.client)
        return search.count()

    def get_last_document_creatiedatum(self) -> str:
        """
        Return the latest creatiedatum of documents in Elasticsearch
        """
        response = self.client.search(
            index=self.index,
            size=0,
            query={"exists": {"field": "creatiedatum"}},
            aggs={"latest_date": {"max": {"field": "creatiedatum"}}},
        )
        return (
            response.get("aggregations", {})
            .get("latest_date", {})
            .get("value_as_string", "")
        )

    def get_last_zaak_registratiedatum(self) -> str:
        """
        Return the second latest distinct registratiedatum of zaken in Elasticsearch.
        This ensures all zaken from the latest date are included when fetching with registratiedatum__gt.
        """
        response = self.client.search(
            index=self.zaak_index,
            size=0,
            query={"exists": {"field": "registratiedatum"}},
            aggs={
                "dates": {
                    "terms": {
                        "field": "registratiedatum",
                        "size": 2,
                        "order": {"_key": "desc"},
                    }
                }
            },
        )

        dates = response.get("aggregations", {}).get("dates", {}).get("buckets", [])

        if len(dates) < 2:
            return ""  # no second last date, fallback to empty

        return dates[1]["key_as_string"]

    def index_document(self, document: Document) -> None:
        if (
            document.inhoud
            and document.bestandsomvang
            and document.bestandsomvang <= settings.SEARCH_INDEX["MAX_INDEX_FILE_SIZE"]
        ):
            document.document_data = download_document(document_url=document.inhoud)

        # TODO check if create or raise error ?
        Document.init(using=self.client)
        document.save(
            id=str(document.uuid),
            using=self.client,
            refresh=settings.SEARCH_INDEX["REFRESH"],
            pipeline=DOCUMENT_ATTACHMENT_PIPELINE_ID,
        )

    def get_document(self, uuid: str) -> Document | None:
        """
        Retrieve a Document from Elasticsearch by its UUID.
        """
        try:
            return Document.get(id=uuid, using=self.client)
        except NotFoundError:
            return None
        except Exception:
            logger.error("failed_to_fetch_document")
            return None

    def get_zaak(self, uuid: str) -> Zaak | None:
        """
        Retrieve a Zaak from Elasticsearch by its UUID.
        """
        try:
            return Zaak.get(id=uuid, using=self.client)
        except NotFoundError:
            return None
        except Exception:
            logger.error("failed_to_fetch_zaak")
            return None

    def delete_document(self, uuid: str) -> bool:
        """
        Delete a Document from Elasticsearch by its UUID.
        """
        try:
            doc = Document.get(id=uuid, using=self.client)
            doc.delete(using=self.client, refresh=settings.SEARCH_INDEX["REFRESH"])
            return True
        except NotFoundError:
            return False
        except Exception:
            logger.error("failed_to_delete_document")
            return False

    def update_verloopt_op(self, uuid: str, new_expiry: datetime) -> bool:
        """
        Update the verloopt_op field for a document.
        """
        try:
            self.client.update(
                index=self.index,
                id=uuid,
                body={"doc": {"verloopt_op": new_expiry}},
                refresh=self._settings["REFRESH"],
            )
            return True
        except NotFoundError:
            return False
        except Exception:
            logger.exception("failed_to_update_verloopt_op", uuid=uuid)
            return False

    def get_expired_document(self, now: datetime, batch_size: int = 100) -> list[str]:
        """
        Retrieve UUIDs of expired documents.
        """
        try:
            response = self.client.search(
                index=self.index,
                size=batch_size,
                _source=False,
                query={"range": {"verloopt_op": {"lte": now}}},
            )
            return [hit["_id"] for hit in response["hits"]["hits"]]
        except Exception:
            logger.exception("failed_to_fetch_expired_document_ids")
            return []

    def index_zaken(
        self, zaak: Zaak, service_slug: str, group_slug: str | None
    ) -> None:
        zaak.service_slug = service_slug
        zaak.group_slug = group_slug
        zaak.save(
            id=str(zaak.uuid),
            using=self.client,
            refresh=settings.SEARCH_INDEX["REFRESH"],
        )


def get_elasticsearch_client() -> ElasticSearchClient:
    return ElasticSearchClient()
