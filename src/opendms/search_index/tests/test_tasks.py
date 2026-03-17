from datetime import UTC, date, datetime

from django.test import override_settings

from celery import current_app
from celery.schedules import crontab
from elasticsearch import NotFoundError
from freezegun import freeze_time
from maykin_common.vcr import VCRMixin

from opendms.api.clients.documenten import get_documenten_client
from opendms.api.tests.factories import ServiceFactory, ZGWApiGroupConfigFactory

from ..client import get_elasticsearch_client
from ..document_task import index_all_documents, search_last_document_creatiedatum
from ..index import Document
from ..tasks import (
    index_document,
    remove_document_from_index,
)
from .base import ElasticSearchAPITestCase, ElasticSearchTestCase
from .factories import IndexDocumentFactory


class DocumentTaskTest(VCRMixin, ElasticSearchTestCase):
    def test_index_document_roundtrip(self):
        document_uuid = "0095704d-4216-4de3-83d2-20dba551b0dc"

        index_document(
            uuid=document_uuid,
            url="http://localhost/document/c80fcb40-f6af-44a4-90ab-07f75b47e9cb",
            identificatie="d481bea6-335b-4d90-9b27-ac49f7196633",
            bronorganisatie="Utrecht",
            creatiedatum=date(2026, 1, 1),
            titel="A test document",
            auteur="Test Author",
            taal="nl",
            begin_registratie=datetime(2026, 1, 5, 12, 0, 0, tzinfo=UTC),
            informatieobjecttype="document",
            vertrouwelijkheidaanduiding=None,
            status="concept",
            formaat="pdf",
            bestandsnaam="document.pdf",
            link=None,
            beschrijving="Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
            verschijningsvorm=None,
            bestandsomvang=1000,  # was file_size
        )

        # verify that it's indexed
        with get_elasticsearch_client() as client:
            doc = Document.get(
                using=client,
                id=document_uuid,
            )

        # helps with type narrowing :)
        assert isinstance(doc, Document), "Expected doc to be indexed"
        # Assert the provided data is indexed properly.
        self.assertEqual(doc.uuid, document_uuid)
        self.assertEqual(
            doc.url, "http://localhost/document/c80fcb40-f6af-44a4-90ab-07f75b47e9cb"
        )
        self.assertEqual(doc.identificatie, "d481bea6-335b-4d90-9b27-ac49f7196633")
        self.assertEqual(doc.bronorganisatie, "Utrecht")

        self.assertEqual(doc.titel, "A test document")
        self.assertEqual(
            doc.beschrijving,
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
        )
        self.assertEqual(doc.auteur, "Test Author")
        self.assertEqual(doc.taal, "nl")

        self.assertIsNone(doc.vertrouwelijkheidaanduiding)
        self.assertEqual(doc.status, "concept")
        self.assertEqual(doc.formaat, "pdf")
        self.assertEqual(doc.bestandsnaam, "document.pdf")
        self.assertEqual(doc.informatieobjecttype, "document")
        self.assertIsNone(doc.verschijningsvorm)

        self.assertIsNone(doc.link)

        self.assertEqual(doc.creatiedatum, date(2026, 1, 1))

        self.assertEqual(
            doc.begin_registratie,
            datetime(2026, 1, 5, 12, 0, 0, tzinfo=UTC),
        )

        with self.subTest("re-indexing data with same UUID updates values"):
            index_document(
                uuid=document_uuid,
                url="http://localhost/document/changed",
                identificatie="changed-id",
                bronorganisatie="Amsterdam",
                creatiedatum=date(2030, 1, 1),
                titel="CHANGED TITLE",
                auteur="Changed Author",
                taal="en",
                begin_registratie=datetime(2030, 1, 5, 12, 0, 0, tzinfo=UTC),
                informatieobjecttype="changed",
                vertrouwelijkheidaanduiding="intern",
                status="published",
                formaat="docx",
                bestandsnaam="changed.docx",
                link="http://example.com",
                beschrijving="Changed description",
                verschijningsvorm=None,
                bestandsomvang=500,
            )

            with get_elasticsearch_client() as client:
                updated_doc = Document.get(
                    using=client,
                    id=document_uuid,
                )

            assert isinstance(updated_doc, Document), "Expected doc to be indexed"

            self.assertEqual(updated_doc.titel, "CHANGED TITLE")
            self.assertEqual(updated_doc.bronorganisatie, "Amsterdam")
            self.assertEqual(updated_doc.formaat, "docx")
            self.assertEqual(updated_doc.status, "published")
            self.assertEqual(updated_doc.creatiedatum, date(2030, 1, 1))

    def test_full_text_upload(self):
        ServiceFactory.create(for_download_url_mock_service=True)
        with self.subTest("Happy flow"):
            document_uuid = "e90b8ea2-1ac2-4ef9-80ed-059d69eb3c54"

            index_document(
                uuid=document_uuid,
                url="http://localhost/document/c80fcb40-f6af-44a4-90ab-07f75b47e9cb",
                identificatie="d481bea6-335b-4d90-9b27-ac49f7196633",
                bronorganisatie="Utrecht",
                creatiedatum=date(2026, 1, 1),
                titel="A test document",
                auteur="Test Author",
                taal="nl",
                begin_registratie=datetime(2026, 1, 5, 12, 0, 0, tzinfo=UTC),
                informatieobjecttype="document",
                vertrouwelijkheidaanduiding=None,
                status="concept",
                formaat="pdf",
                bestandsnaam="document.pdf",
                inhoud="http://localhost/document/c80fcb40-f6af-44a4-90ab-07f75b47e9cb",
                link=None,
                beschrijving="Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
                verschijningsvorm=None,
                bestandsomvang=1000,
            )

            # verify that it's indexed
            with get_elasticsearch_client() as client:
                doc_source = client.get(index="document", id=document_uuid)["_source"]

            self.assertEqual(
                doc_source["document_data"][0]["attachment"]["content"],
                "Document 'c80fcb40-f6af-44a4-90ab-07f75b47e9cb'",
            )

        with self.subTest(
            "Download url with no content doesn't create attachment field in index."
        ):
            document_uuid = "9acc8148-b498-4c15-b2df-0f26d41ff4c2"

            index_document(
                uuid=document_uuid,
                url="http://localhost/document/c80fcb40-f6af-44a4-90ab-07f75b47e9cb",
                identificatie="d481bea6-335b-4d90-9b27-ac49f7196633",
                bronorganisatie="Utrecht",
                creatiedatum=date(2026, 1, 1),
                titel="A test document",
                auteur="Test Author",
                taal="nl",
                begin_registratie=datetime(2026, 1, 5, 12, 0, 0, tzinfo=UTC),
                informatieobjecttype="document",
                vertrouwelijkheidaanduiding=None,
                status="concept",
                formaat="pdf",
                bestandsnaam="document.pdf",
                inhoud="http://localhost/document/empty",
                link=None,
                beschrijving="Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
                verschijningsvorm=None,
                bestandsomvang=1000,
            )

            # verify that it's indexed
            with get_elasticsearch_client() as client:
                doc_source = client.get(index="document", id=document_uuid)["_source"]

            self.assertEqual(doc_source["document_data"][0]["attachment"], {})

        with self.subTest(
            "Download url raises error creates empty attachment field in index."
        ):
            document_uuid = "9acc8148-b498-4c15-b2df-0f26d41ff4c2"

            index_document(
                uuid=document_uuid,
                url="http://localhost/document/c80fcb40-f6af-44a4-90ab-07f75b47e9cb",
                identificatie="d481bea6-335b-4d90-9b27-ac49f7196633",
                bronorganisatie="Utrecht",
                creatiedatum=date(2026, 1, 1),
                titel="A test document",
                auteur="Test Author",
                taal="nl",
                begin_registratie=datetime(2026, 1, 5, 12, 0, 0, tzinfo=UTC),
                informatieobjecttype="document",
                vertrouwelijkheidaanduiding=None,
                status="concept",
                formaat="pdf",
                bestandsnaam="document.pdf",
                inhoud="http://localhost/document/error",
                link=None,
                beschrijving="Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
                verschijningsvorm=None,
                bestandsomvang=1000,
            )

            # verify that it's indexed
            with get_elasticsearch_client() as client:
                doc_source = client.get(index="document", id=document_uuid)["_source"]

            self.assertNotIn("document_data", doc_source)

    def test_full_text_upload_download_url_service_unauthorized(self):
        ServiceFactory.create(
            for_download_url_mock_service=True, header_value="Token wrong-token"
        )

        document_uuid = "9acc8148-b498-4c15-b2df-0f26d41ff4c2"

        index_document(
            uuid=document_uuid,
            url="http://localhost/document/c80fcb40-f6af-44a4-90ab-07f75b47e9cb",
            identificatie="d481bea6-335b-4d90-9b27-ac49f7196633",
            bronorganisatie="Utrecht",
            creatiedatum=date(2026, 1, 1),
            titel="A test document",
            auteur="Test Author",
            taal="nl",
            begin_registratie=datetime(2026, 1, 5, 12, 0, 0, tzinfo=UTC),
            informatieobjecttype="document",
            vertrouwelijkheidaanduiding=None,
            status="concept",
            formaat="pdf",
            bestandsnaam="document.pdf",
            inhoud="https://www.example.com/downloads/1",
            link=None,
            beschrijving="Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
            verschijningsvorm=None,
            bestandsomvang=1000,
        )

        # verify that it's indexed
        with get_elasticsearch_client() as client:
            doc_source = client.get(index="document", id=document_uuid)["_source"]

        self.assertNotIn("document_data", doc_source)

    @override_settings(
        SEARCH_INDEX={
            "HOST": "http://localhost:9201",
            "USER": "",
            "PASSWORD": "",
            "TIMEOUT": 3,
            "CA_CERTS": "",
            "REFRESH": "wait_for",
            "INDEXED_CHARS": -1,
            "MAX_INDEX_FILE_SIZE": 1000,  # byte
        }
    )
    def test_full_text_upload_with_max_file_size(self):
        ServiceFactory.create(for_download_url_mock_service=True)

        with self.subTest(
            "Don't index full document text when no bestandsomvang was given."
        ):
            document_uuid = "ed19d46e-c367-4410-a891-88f20d232a03"

            index_document(
                uuid=document_uuid,
                url="http://localhost/document/c80fcb40-f6af-44a4-90ab-07f75b47e9cb",
                identificatie="d481bea6-335b-4d90-9b27-ac49f7196633",
                bronorganisatie="Utrecht",
                creatiedatum=date(2026, 1, 1),
                titel="A test document",
                auteur="Test Author",
                taal="nl",
                begin_registratie=datetime(2026, 1, 5, 12, 0, 0, tzinfo=UTC),
                informatieobjecttype="document",
                vertrouwelijkheidaanduiding=None,
                status="concept",
                formaat="pdf",
                bestandsnaam="document.pdf",
                inhoud="http://localhost/document/c80fcb40-f6af-44a4-90ab-07f75b47e9cb",
                link=None,
                beschrijving="Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
                verschijningsvorm=None,
            )

            # verify that it's indexed
            with get_elasticsearch_client() as client:
                doc_source = client.get(index="document", id=document_uuid)["_source"]

            self.assertNotIn("document_data", doc_source)

        with self.subTest(
            "if given file_size is higher then max_file_size don't index full "
            "document text."
        ):
            document_uuid = "da97b6cb-7211-4762-9673-21a08f508e85 "

            index_document(
                uuid=document_uuid,
                url="http://localhost/document/c80fcb40-f6af-44a4-90ab-07f75b47e9cb",
                identificatie="d481bea6-335b-4d90-9b27-ac49f7196633",
                bronorganisatie="Utrecht",
                creatiedatum=date(2026, 1, 1),
                titel="A test document",
                auteur="Test Author",
                taal="nl",
                begin_registratie=datetime(2026, 1, 5, 12, 0, 0, tzinfo=UTC),
                informatieobjecttype="document",
                vertrouwelijkheidaanduiding=None,
                status="concept",
                formaat="pdf",
                bestandsnaam="document.pdf",
                inhoud="http://localhost/document/c80fcb40-f6af-44a4-90ab-07f75b47e9cb",
                link=None,
                beschrijving="Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
                verschijningsvorm=None,
                bestandsomvang=2000,
            )

            # verify that it's indexed
            with get_elasticsearch_client() as client:
                doc_source = client.get(index="document", id=document_uuid)["_source"]

            self.assertNotIn("attachment", doc_source)

        with self.subTest(
            "index full document text if file size is lower then the max configured "
            "size."
        ):
            document_uuid = "554be64c-e6af-49b5-8af5-80e83155212d"

            index_document(
                uuid=document_uuid,
                url="http://localhost/document/c80fcb40-f6af-44a4-90ab-07f75b47e9cb",
                identificatie="d481bea6-335b-4d90-9b27-ac49f7196633",
                bronorganisatie="Utrecht",
                creatiedatum=date(2026, 1, 1),
                titel="A test document",
                auteur="Test Author",
                taal="nl",
                begin_registratie=datetime(2026, 1, 5, 12, 0, 0, tzinfo=UTC),
                informatieobjecttype="document",
                vertrouwelijkheidaanduiding=None,
                status="concept",
                formaat="pdf",
                bestandsnaam="document.pdf",
                inhoud="http://localhost/document/c80fcb40-f6af-44a4-90ab-07f75b47e9cb",
                link=None,
                beschrijving="Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
                verschijningsvorm=None,
                bestandsomvang=800,
            )

            # verify that it's indexed
            with get_elasticsearch_client() as client:
                doc_source = client.get(index="document", id=document_uuid)["_source"]

            self.assertEqual(
                doc_source["document_data"][0]["attachment"]["content"],
                "Document 'c80fcb40-f6af-44a4-90ab-07f75b47e9cb'",
            )

    def test_update_full_document_text(self):
        ServiceFactory.create(for_download_url_mock_service=True)
        document_uuid = "e62db63f-9e99-41a4-88a9-be9cc3d7509a"

        index_document(
            uuid=document_uuid,
            url="http://localhost/document/c80fcb40-f6af-44a4-90ab-07f75b47e9cb",
            identificatie="d481bea6-335b-4d90-9b27-ac49f7196633",
            bronorganisatie="Utrecht",
            creatiedatum=date(2026, 1, 1),
            titel="A test document",
            auteur="Test Author",
            taal="nl",
            begin_registratie=datetime(2026, 1, 5, 12, 0, 0, tzinfo=UTC),
            informatieobjecttype="document",
            vertrouwelijkheidaanduiding=None,
            status="concept",
            formaat="pdf",
            bestandsnaam="document.pdf",
            inhoud="http://localhost/document/ff2c18cf-8165-45d3-873d-b68e676f99ff",
            link=None,
            beschrijving="Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
            verschijningsvorm=None,
            bestandsomvang=1000,
        )

        # verify that it's indexed
        with get_elasticsearch_client() as client:
            doc_source = client.get(index="document", id=document_uuid)["_source"]

        self.assertEqual(
            doc_source["document_data"][0]["attachment"]["content"],
            "Document 'ff2c18cf-8165-45d3-873d-b68e676f99ff'",
        )

        # Update document data by changing response content from url
        index_document(
            uuid=document_uuid,
            url="http://localhost/document/c80fcb40-f6af-44a4-90ab-07f75b47e9cb",
            identificatie="d481bea6-335b-4d90-9b27-ac49f7196633",
            bronorganisatie="Utrecht",
            creatiedatum=date(2026, 1, 1),
            titel="A test document",
            auteur="Test Author",
            taal="nl",
            begin_registratie=datetime(2026, 1, 5, 12, 0, 0, tzinfo=UTC),
            informatieobjecttype="document",
            vertrouwelijkheidaanduiding=None,
            status="concept",
            formaat="pdf",
            bestandsnaam="document.pdf",
            inhoud="http://localhost/document/8decfefc-9879-45e8-8641-2096bbd5dba8",
            link=None,
            beschrijving="Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
            verschijningsvorm=None,
            bestandsomvang=1000,
        )

        # verify that it's indexed
        with get_elasticsearch_client() as client:
            doc_source = client.get(index="document", id=document_uuid)["_source"]

        self.assertEqual(
            doc_source["document_data"][0]["attachment"]["content"],
            "Document '8decfefc-9879-45e8-8641-2096bbd5dba8'",
        )

    def test_download_zip_document(self):
        ServiceFactory.create(for_download_url_mock_service=True)
        document_uuid = "f5a98468-92ef-49a1-8dff-4a7c682347f8"

        index_document(
            uuid=document_uuid,
            url="http://localhost/document/c80fcb40-f6af-44a4-90ab-07f75b47e9cb",
            identificatie="d481bea6-335b-4d90-9b27-ac49f7196633",
            bronorganisatie="Utrecht",
            creatiedatum=date(2026, 1, 1),
            titel="A test document",
            auteur="Test Author",
            taal="nl",
            begin_registratie=datetime(2026, 1, 5, 12, 0, 0, tzinfo=UTC),
            informatieobjecttype="document",
            vertrouwelijkheidaanduiding=None,
            status="concept",
            formaat="pdf",
            bestandsnaam="document.pdf",
            inhoud="http://localhost/document/zip",
            link=None,
            beschrijving="Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
            verschijningsvorm=None,
            bestandsomvang=1000,
        )
        # verify that it's indexed
        with get_elasticsearch_client() as client:
            doc_source = client.get(index="document", id=document_uuid)["_source"]

        self.assertEqual(len(doc_source["document_data"]), 2)
        self.assertEqual(
            doc_source["document_data"][0]["attachment"]["content"],
            "test1",
        )
        self.assertEqual(
            doc_source["document_data"][1]["attachment"]["content"],
            "test2",
        )

    @override_settings(
        SEARCH_INDEX={
            "HOST": "http://localhost:9201",
            "USER": "",
            "PASSWORD": "",
            "TIMEOUT": 3,
            "CA_CERTS": "",
            "REFRESH": "wait_for",
            "INDEXED_CHARS": -1,
            "MAX_INDEX_FILE_SIZE": 1000,  # byte
        }
    )
    def test_download_7zip_document(self):
        ServiceFactory.create(for_download_url_mock_service=True)
        document_uuid = "d9fe4844-bdf8-4d66-b613-4efa71598105"

        index_document(
            uuid=document_uuid,
            url="http://localhost/document/c80fcb40-f6af-44a4-90ab-07f75b47e9cb",
            identificatie="d481bea6-335b-4d90-9b27-ac49f7196633",
            bronorganisatie="Utrecht",
            creatiedatum=date(2026, 1, 1),
            titel="A test document",
            auteur="Test Author",
            taal="nl",
            begin_registratie=datetime(2026, 1, 5, 12, 0, 0, tzinfo=UTC),
            informatieobjecttype="document",
            vertrouwelijkheidaanduiding=None,
            status="concept",
            formaat="pdf",
            bestandsnaam="document.pdf",
            inhoud="http://localhost/document/7zip",
            link=None,
            beschrijving="Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
            verschijningsvorm=None,
            bestandsomvang=401,
        )

        # verify that it's indexed
        with get_elasticsearch_client() as client:
            doc_source = client.get(index="document", id=document_uuid)["_source"]

        # test that only files up to 1000 bytes get indexed.
        # This excludes the test3 file which is 1mb.
        self.assertEqual(len(doc_source["document_data"]), 2)
        self.assertEqual(
            doc_source["document_data"][0]["attachment"]["content"],
            "test1",
        )
        self.assertEqual(
            doc_source["document_data"][1]["attachment"]["content"],
            "test2",
        )

    @override_settings(
        SEARCH_INDEX={
            "HOST": "http://localhost:9201",
            "USER": "",
            "PASSWORD": "",
            "TIMEOUT": 3,
            "CA_CERTS": "",
            "REFRESH": "wait_for",
            "INDEXED_CHARS": -1,
            "MAX_INDEX_FILE_SIZE": 500,  # byte
        }
    )
    def test_download_7zip_document_file_size_reached(self):
        ServiceFactory.create(for_download_url_mock_service=True)
        document_uuid = "d9fe4844-bdf8-4d66-b613-4efa71598105"

        index_document(
            uuid=document_uuid,
            url="http://localhost/document/c80fcb40-f6af-44a4-90ab-07f75b47e9cb",
            identificatie="d481bea6-335b-4d90-9b27-ac49f7196633",
            bronorganisatie="Utrecht",
            creatiedatum=date(2026, 1, 1),
            titel="A test document",
            auteur="Test Author",
            taal="nl",
            begin_registratie=datetime(2026, 1, 5, 12, 0, 0, tzinfo=UTC),
            informatieobjecttype="document",
            vertrouwelijkheidaanduiding=None,
            status="concept",
            formaat="pdf",
            bestandsnaam="document.pdf",
            inhoud="http://localhost/document/smol7zip",
            link=None,
            beschrijving="Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
            verschijningsvorm=None,
            bestandsomvang=188,
        )

        # verify that it's indexed
        with get_elasticsearch_client() as client:
            doc_source = client.get(index="document", id=document_uuid)["_source"]

        # test that only files up to 5 bytes get indexed - the second file is discarded
        self.assertEqual(len(doc_source["document_data"]), 1)

    def test_full_document_text_index_without_service_configured(self):
        document_uuid = "e62db63f-9e99-41a4-88a9-be9cc3d7509a"

        index_document(
            uuid=document_uuid,
            url="http://localhost/document/c80fcb40-f6af-44a4-90ab-07f75b47e9cb",
            identificatie="d481bea6-335b-4d90-9b27-ac49f7196633",
            bronorganisatie="Utrecht",
            creatiedatum=date(2026, 1, 1),
            titel="A test document",
            auteur="Test Author",
            taal="nl",
            begin_registratie=datetime(2026, 1, 5, 12, 0, 0, tzinfo=UTC),
            informatieobjecttype="document",
            vertrouwelijkheidaanduiding=None,
            status="concept",
            formaat="pdf",
            bestandsnaam="document.pdf",
            inhoud="http://localhost/document/c80fcb40-f6af-44a4-90ab-07f75b47e9cb",
            link=None,
            beschrijving="Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
            verschijningsvorm=None,
            bestandsomvang=1000,
        )

        # verify that it's indexed
        with get_elasticsearch_client() as client:
            doc_source = client.get(index="document", id=document_uuid)["_source"]

        self.assertNotIn("document_data", doc_source)


class RemoveFromIndexTaskTests(VCRMixin, ElasticSearchTestCase):
    def test_remove_non_existing_document(self):
        result = remove_document_from_index("452635a9-228f-4cda-9bec-66310ccbb6a1")

        self.assertIsNone(result)

    def test_remove_indexed_document(self):
        doc = IndexDocumentFactory.build(uuid="ad4d66a8-1503-4743-ae55-d1765512530c")
        index_document(**doc)

        result = remove_document_from_index("ad4d66a8-1503-4743-ae55-d1765512530c")

        self.assertIsNone(result)
        with (
            get_elasticsearch_client() as client,
            self.assertRaises(NotFoundError),
        ):
            Document.get(id="ad4d66a8-1503-4743-ae55-d1765512530c", using=client)


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class IndexAllDocumentsTaskTests(VCRMixin, ElasticSearchAPITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.documenten_service = ServiceFactory.create(
            for_drc_service_docker_compose=True
        )
        ZGWApiGroupConfigFactory.create(
            drc_service=cls.documenten_service,
        )

        cls.documenten_service_2 = ServiceFactory.create(
            for_drc_service_docker_compose=True
        )
        ZGWApiGroupConfigFactory.create(
            drc_service=cls.documenten_service_2,
        )

    def test_indexes_documents(self):
        index_all_documents()

        with get_elasticsearch_client() as client:
            all_docs = Document.search(using=client).execute()
            self.assertGreater(
                len(all_docs), 0, "Expected at least one document indexed"
            )

            doc = all_docs[0]
            self.assertTrue(hasattr(doc, "uuid"))
            self.assertTrue(hasattr(doc, "titel"))
            self.assertTrue(hasattr(doc, "creatiedatum"))

    def test_creatiedatum_prevents_reindexing_by_double_call(self):
        index_all_documents()

        with get_elasticsearch_client() as client:
            all_docs_first = Document.search(using=client).execute()
            uuids_first = [doc.uuid for doc in all_docs_first]

        index_all_documents()

        with get_elasticsearch_client() as client:
            all_docs_second = Document.search(using=client).execute()
            uuids_second = [doc.uuid for doc in all_docs_second]

        self.assertEqual(set(uuids_first), set(uuids_second))

    def test_add_new_document(self):
        index_all_documents()
        with get_elasticsearch_client() as client:
            docs_before = Document.search(using=client).execute()
            count_before = len(docs_before)

        new_docs = [
            IndexDocumentFactory.build(
                uuid="bd4d66a8-1503-4743-ae55-d1765512530c",
            ),
            IndexDocumentFactory.build(
                uuid="rd4d66a8-1503-4743-ae55-d1765512530c",
            ),
        ]
        for doc in new_docs:
            index_document(**doc)

        index_all_documents()
        with get_elasticsearch_client() as client:
            docs_after = Document.search(using=client).execute()
            count_after = len(docs_after)

        self.assertGreater(count_after, count_before)
        uuids_after = [doc.uuid for doc in docs_after]

        self.assertIn("bd4d66a8-1503-4743-ae55-d1765512530c", uuids_after)
        self.assertIn("rd4d66a8-1503-4743-ae55-d1765512530c", uuids_after)

    @freeze_time("2026-03-16 12:00:00+00:00")
    def test_hourly_task(self):
        schedule = current_app.conf.beat_schedule
        task_entry = schedule.get("update_documents_hourly")
        self.assertIsNotNone(task_entry)
        self.assertEqual(
            task_entry["task"], "opendms.search_index.document_task.index_all_documents"
        )
        self.assertIsInstance(task_entry["schedule"], crontab)

        current_app.tasks[task_entry["task"]].apply()

        with get_elasticsearch_client() as client:
            all_docs = Document.search(using=client).execute()
            self.assertGreater(len(all_docs), 0)

    def test_date_filter(self):
        doc1 = IndexDocumentFactory.build(
            uuid="doc-old",
            creatiedatum="2026-03-13",
        )
        index_document(**doc1)

        with get_elasticsearch_client() as client:
            client.indices.refresh(index="document")

        index_all_documents()

        last_creatiedatum = search_last_document_creatiedatum()
        self.assertEqual(last_creatiedatum, "2026-03-13")

        with get_documenten_client(self.documenten_service) as client:
            documents = client.get_items(
                filters={"creatiedatum__gte": last_creatiedatum}
            )

        for doc in documents:
            self.assertGreaterEqual(doc["creatiedatum"], last_creatiedatum)
