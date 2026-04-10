from collections.abc import Collection

from django.test import TestCase, override_settings, tag

import structlog
from elasticsearch.dsl import Document

from opendms.conf.utils import config
from opendms.search_index.client import get_elasticsearch_client
from opendms.search_index.index import Zaak

from ...api.tests.api_testcase import APITestCase
from ..ingest import setup_document_attachment_processor
from ..utils import get_index_document_types

CI = config("CI", default=False)  # Github actions sets this to True

logger = structlog.get_logger(__name__)

override_es_settings = override_settings(
    SEARCH_INDEX={
        "HOST": "http://localhost:9201",  # docker vcr_test
        "USER": "",  # no auth
        "PASSWORD": "",
        "TIMEOUT": 3,
        "CA_CERTS": "",
        "REFRESH": "wait_for",
        "INDEXED_CHARS": -1,
        "MAX_INDEX_FILE_SIZE": 1 * 1000 * 1000,
    }
)


class ElasticSearchMixin:
    """
    Handles setting up test data for Elasticsearch Documents by creating test
    indexes.
    """

    _es_online: bool = True
    _es_indexes: set[str]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()  # pyright: ignore[reportAttributeAccessIssue]

        _index_names: set[str] = set()
        _document_types: Collection[type[Document]] = []
        for subcls in get_index_document_types():
            _index_names.add(subcls.Index.name)
            _document_types.append(subcls)

        cls._es_indexes = _index_names

        # create the indices
        with override_es_settings:
            with get_elasticsearch_client() as es_client:
                cls._es_online = es_client.can_connect
                if not cls._es_online:
                    logger.info(
                        "ES %r is not available. Running in CI: %r.%s",
                        es_client.client,
                        CI,
                        (
                            ""
                            if CI
                            else (
                                " Use `docker/docker-compose.es.yml` to spin up "
                                "the service."
                            )
                        ),
                    )
                else:
                    for _doc_type in _document_types:
                        # create index and mappings
                        _doc_type.init(using=es_client.client)

                    setup_document_attachment_processor(client=es_client.client)

        def teardown():
            if not cls._es_online:
                return
            if not _index_names:
                return
            with override_es_settings:
                with get_elasticsearch_client() as es_client:
                    es_client.client.indices.delete(index=list(_index_names))

        cls.addClassCleanup(teardown)  # pyright: ignore[reportAttributeAccessIssue]

    def setUp(self) -> None:
        super().setUp()  # pyright: ignore[reportAttributeAccessIssue]

        if not self._es_online:
            return

        if not self._es_indexes:
            return

        with override_es_settings:
            with get_elasticsearch_client() as es_client:
                # empty index before tests
                es_client.client.delete_by_query(
                    index=list(self._es_indexes),
                    body={"query": {"match_all": {}}},
                    ignore_unavailable=True,
                    conflicts="proceed",
                    refresh=True,
                )


@tag("elasticsearch")
@override_es_settings
class ElasticSearchTestCase(ElasticSearchMixin, TestCase):
    """
    Django TestCase subclass with setup and teardown for elastic search cluster.
    """


@tag("elasticsearch")
@override_es_settings
class ElasticSearchAPITestCase(ElasticSearchMixin, APITestCase):
    """
    DRC APITestCase subclass with setup and teardown for elastic search cluster.
    """

    def index_document(self, document: Document):
        with get_elasticsearch_client() as client:
            client.index_document(document)

    def index_zaak(self, zaak: Zaak):
        service = "test-service"
        group_slug = "test-group"
        with get_elasticsearch_client() as client:
            client.index_zaken(zaak, service_slug=service, group_slug=group_slug)
