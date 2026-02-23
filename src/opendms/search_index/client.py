import os
import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from typing import Literal, assert_never
from urllib.parse import urlsplit

from django.conf import settings

from elasticsearch import Elasticsearch
from elasticsearch.dsl import Q, Search

from .index import Document
from .typing import IndexName

__all__ = ["get_client", "get_search_results"]


def get_client() -> Elasticsearch:
    host = settings.SEARCH_INDEX["HOST"]
    username = settings.SEARCH_INDEX["USER"]
    password = settings.SEARCH_INDEX["PASSWORD"]
    basic_auth = (username, password) if username else None

    # REQUESTS_CA_BUNDLE is set by self-certifi OR could be set at deployment time, acts
    # as default if no explicit CA is specified.
    ca_certs: str | None = settings.SEARCH_INDEX["CA_CERTS"] or os.environ.get(
        "REQUESTS_CA_BUNDLE"
    )

    # can't just fallback to ca_certs=None since it has special meaning
    extra = {}
    if ca_certs and urlsplit(host).scheme == "https":  # pragma: no cover
        extra["ca_certs"] = ca_certs

    return Elasticsearch(
        host,
        basic_auth=basic_auth,
        timeout=settings.SEARCH_INDEX["TIMEOUT"],
        **extra,
    )


@dataclass
class SearchResult:
    type: IndexName
    record: Document


@dataclass
class SearchResults:
    total_count: int
    results: Sequence[SearchResult]


def clean_str_query(query: str) -> str:
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


def get_search_results(
    # query
    query: str,
    # filters
    creatiedatum_from: date | None = None,
    creatiedatum_to: date | None = None,
    page: int = 1,
    page_size: int = 10,
    sort: Literal["relevance", "chronological"] = "relevance",
) -> SearchResults:
    """
    Perform the search query in elastic search.

    The filter/query parameters are translated into an Elastic Search query,
    which is executed agains the configured ES cluster. The results are then
    collected and returned so they can be post-processed if needed.
    """

    # build up the search object from the provided arguments
    search = Search().doc_type(Document).index(Document.Index.name)

    # process the query (terms)
    if query:
        search = search.query(
            "simple_query_string",
            query=clean_str_query(query),
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

    if creatiedatum_from or creatiedatum_to:
        search = search.filter(
            "range",
            creatiedatum={"gte": creatiedatum_from, "lte": creatiedatum_to},
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
                    "begin_registratie": {
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
    with get_client() as client:
        search = search.using(client)
        response = search.execute()

    # process the results
    results = [
        SearchResult(
            type=hit.meta.index,
            # ES-DSL typing isn't fancy enough yet...
            record=hit,  # pyright: ignore[reportArgumentType]
        )
        for hit in response.hits
    ]

    return SearchResults(
        total_count=response.hits.total.value,  # pyright: ignore[reportAttributeAccessIssue]
        results=results,
    )
