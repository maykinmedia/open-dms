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

from .constants import DOCUMENT_ATTACHMENT_PIPELINE_ID, DOCUMENT_INDEX
from .index import Document, DocumentResults
from .utils import download_document

logger = structlog.get_logger(__name__)


class ElasticSearchClient:
    # TODO add check if index exists, if not create it
    index = DOCUMENT_INDEX

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
    ) -> DocumentResults:
        """
        Perform the search query in Elasticsearch using the DSL Search object.
        """

        # TODO check if you can have different INDICES
        search = Search(index=Document.Index.name, doc_type=Document)

        if query:
            doc_query = Q(
                "simple_query_string",
                query=self._clean_str_query(query),
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
            zaak_query = Q(
                "nested",
                path="zaak_referenties",
                query=Q(
                    "simple_query_string",
                    query=self._clean_str_query(query),
                    fields=[
                        "zaak_referenties.identificatie^3",
                        "zaak_referenties.omschrijving^2",
                        "zaak_referenties.toelichting^1.5",
                        "zaak_referenties.status^1.2",
                    ],
                    flags="OR|AND|PHRASE|PRECEDENCE|WHITESPACE",
                    default_operator="AND",
                ),
            )

            search = search.query(
                Q("bool", should=[doc_query, zaak_query], minimum_should_match=1)
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

        # bind it to the client containing the connection details
        search = search.using(self.client)
        response = search.execute()

        # process the results
        return DocumentResults(
            total_count=response.hits.total.value,  # pyright: ignore[reportAttributeAccessIssue]
            results=[hit for hit in response.hits],
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

    def get_total_count(self) -> int:
        """
        Count documents in the index
        """

        search = Search(index=self.index, doc_type=Document).using(self.client)
        return search.count()

    def get_last_document_creatiedatum(self, service_slug: str | None = None) -> str:
        """
        Return the latest creatiedatum of documents in Elasticsearch,
        optionally filtered by service_slug.
        """
        query = {"exists": {"field": "creatiedatum"}}
        if service_slug:
            query = {
                "bool": {"must": [query, {"term": {"service_slug": service_slug}}]}
            }

        response = self.client.search(
            index=self.index,
            size=0,
            query=query,
            aggs={"latest_date": {"max": {"field": "creatiedatum"}}},
        )

        return (
            response.get("aggregations", {})
            .get("latest_date", {})
            .get("value_as_string", "")
        )

    def index_document(
        self, document: Document, service: str, group_slug: str | None
    ) -> None:
        if (
            document.inhoud
            and document.bestandsomvang
            and document.bestandsomvang <= settings.SEARCH_INDEX["MAX_INDEX_FILE_SIZE"]
        ):
            document.document_data = download_document(document_url=document.inhoud)

        document.service_slug = service
        document.group_slug = group_slug

        # TODO check if create or raise error ?
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

    def update_check_times(
        self, uuid: str, last_checked_at: datetime, next_check_at: datetime
    ) -> bool:
        """
        Update the check times for a document.
        """
        try:
            self.client.update(
                index=self.index,
                id=uuid,
                body={
                    "doc": {
                        "last_checked_at": last_checked_at,
                        "next_check_at": next_check_at,
                    }
                },
                refresh=self._settings["REFRESH"],
            )
            return True
        except NotFoundError:
            return False
        except Exception:
            logger.exception("failed_to_update_update_check_times", uuid=uuid)
            return False

    def get_expired_documents(
        self, now: datetime, batch_size: int = 100, service_slug: str | None = None
    ) -> list[dict]:
        """
        Retrieve expired documents with UUID, service_slug, and group_slug.
        """
        try:
            query = {"range": {"next_check_at": {"lte": now}}}
            if service_slug:
                query = {
                    "bool": {"must": [query, {"term": {"service_slug": service_slug}}]}
                }
            response = self.client.search(
                index=self.index,
                size=batch_size,
                _source=["service_slug", "group_slug", "creatiedatum"],
                query=query,
            )
            hits = response.get("hits", {}).get("hits", [])
            results = []

            for hit in hits:
                source = hit.get("_source", {})
                results.append(
                    {
                        "uuid": hit.get("_id"),
                        "service_slug": source.get("service_slug"),
                        "group_slug": source.get("group_slug"),
                        "creatiedatum": source.get("creatiedatum"),
                    }
                )

            return results

        except Exception:
            logger.exception("failed_to_fetch_expired_documents")
            return []


def get_elasticsearch_client() -> ElasticSearchClient:
    return ElasticSearchClient()
