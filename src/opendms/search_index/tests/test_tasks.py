from datetime import UTC, date, datetime, timedelta
from unittest.mock import patch

from django.test import override_settings

from celery import current_app
from freezegun import freeze_time
from maykin_common.vcr import VCRMixin

from opendms.api.models import ZGWApiGroupConfig
from opendms.api.tests.factories import ServiceFactory, ZGWApiGroupConfigFactory
from opendms.api.utils.exceptions import ExternalServiceUnavailable

from ..client import get_elasticsearch_client
from ..document_task import (
    index_all_documents,
    validate_expired_documents,
)
from ..index import Document
from .base import ElasticSearchAPITestCase, ElasticSearchTestCase
from .factories import IndexDocumentFactory


# TODO create tests for client
# TODO create tests for tasks
# TODO check codecov tests
class DocumentTaskTest(VCRMixin, ElasticSearchTestCase):
    def test_index_document_roundtrip(self):
        document_uuid = "0095704d-4216-4de3-83d2-20dba551b0dc"
        with get_elasticsearch_client() as client:
            doc = IndexDocumentFactory(
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
                last_checked_at=date(2026, 1, 1),
                next_check_at=date(2026, 1, 5),
            )

            client.index_document(doc, service="documenten-api", group_slug="group-1")

            doc = client.get_document(document_uuid)

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
            doc = IndexDocumentFactory(
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
                last_checked_at=date(2026, 1, 1),
                next_check_at=date(2026, 1, 5),
            )

            with get_elasticsearch_client() as client:
                client.index_document(
                    doc, service="documenten-api", group_slug="group-1"
                )
                updated_doc = client.get_document(document_uuid)

            assert isinstance(updated_doc, Document), "Expected doc to be indexed"

            self.assertEqual(updated_doc.titel, "CHANGED TITLE")
            self.assertEqual(updated_doc.bronorganisatie, "Amsterdam")
            self.assertEqual(updated_doc.formaat, "docx")
            self.assertEqual(updated_doc.status, "published")
            self.assertEqual(updated_doc.creatiedatum, date(2030, 1, 1))

    def test_text_upload_happy_flow(self):
        ServiceFactory.create(for_download_url_mock_service=True)
        document_uuid = "e90b8ea2-1ac2-4ef9-80ed-059d69eb3c54"
        doc = IndexDocumentFactory(
            uuid=document_uuid,
            inhoud="http://localhost/document/c80fcb40-f6af-44a4-90ab-07f75b47e9cb",
        )

        # verify that it's indexed
        with get_elasticsearch_client() as client:
            client.index_document(doc, service="documenten-api", group_slug="group-1")
            doc_obj = client.get_document(document_uuid)
        self.assertEqual(
            doc_obj.document_data[0].attachment.content,
            "Document 'c80fcb40-f6af-44a4-90ab-07f75b47e9cb'",
        )

    def test_text_upload_no_content(self):
        ServiceFactory.create(for_download_url_mock_service=True)
        document_uuid = "9acc8148-b498-4c15-b2df-0f26d41ff4c2"
        doc = IndexDocumentFactory(
            uuid=document_uuid, inhoud="http://localhost/document/empty"
        )

        # verify that it's indexed
        with get_elasticsearch_client() as client:
            client.index_document(doc, service="documenten-api", group_slug="group-1")
            doc_obj = client.get_document(document_uuid)

        self.assertEqual(doc_obj.document_data[0].attachment, {})

    def test_text_upload_service_raise_error(self):
        ServiceFactory.create(for_download_url_mock_service=True)
        document_uuid = "9acc8148-b498-4c15-b2df-0f26d41ff4c2"
        doc = IndexDocumentFactory(
            uuid=document_uuid, inhoud="http://localhost/document/error"
        )

        # verify that it's indexed
        with get_elasticsearch_client() as client:
            client.index_document(doc, service="documenten-api", group_slug="group-1")
            doc_obj = client.get_document(document_uuid)
        self.assertEqual(doc_obj.document_data, {})

    def test_text_upload_service_not_configured(self):
        document_uuid = "9acc8148-b498-4c15-b2df-0f26d41ff4c2"
        doc = IndexDocumentFactory(
            uuid=document_uuid,
            inhoud="http://localhost/document/c80fcb40-f6af-44a4-90ab-07f75b47e9cb",
        )

        # verify that it's indexed
        with get_elasticsearch_client() as client:
            client.index_document(doc, service="documenten-api", group_slug="group-1")
            doc_obj = client.get_document(document_uuid)
        self.assertEqual(doc_obj.document_data, {})

    def test_text_upload_service_unauthorized(self):
        ServiceFactory.create(
            for_download_url_mock_service=True, header_value="Token wrong-token"
        )
        document_uuid = "9acc8148-b498-4c15-b2df-0f26d41ff4c2"
        doc = IndexDocumentFactory(
            uuid=document_uuid, inhoud="https://www.example.com/downloads/1"
        )

        # verify that it's indexed
        with get_elasticsearch_client() as client:
            client.index_document(doc, service="documenten-api", group_slug="group-1")
            doc_obj = client.get_document(document_uuid)
        self.assertEqual(doc_obj.document_data, {})

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
    def test_text_upload_with_max_file_size(self):
        ServiceFactory.create(for_download_url_mock_service=True)
        with self.subTest(
            "Don't index full document text when no bestandsomvang was given."
        ):
            document_uuid = "ed19d46e-c367-4410-a891-88f20d232a03"
            doc = IndexDocumentFactory(
                uuid=document_uuid,
                inhoud="http://localhost/document/c80fcb40-f6af-44a4-90ab-07f75b47e9cb",
                # bestandsomvang default from factory is < MAX_INDEX_FILE_SIZE
            )

            # verify that it's indexed
            with get_elasticsearch_client() as client:
                client.index_document(
                    doc, service="documenten-api", group_slug="group-1"
                )
                doc_obj = client.get_document(document_uuid)

            self.assertEqual(doc_obj.document_data, {})

        with self.subTest(
            "if given file_size is higher then max_file_size don't index full "
            "document text."
        ):
            document_uuid = "da97b6cb-7211-4762-9673-21a08f508e85 "
            doc = IndexDocumentFactory(
                uuid=document_uuid,
                inhoud="http://localhost/document/c80fcb40-f6af-44a4-90ab-07f75b47e9cb",
                bestandsomvang=2000,
            )

            # verify that it's indexed
            with get_elasticsearch_client() as client:
                client.index_document(
                    doc, service="documenten-api", group_slug="group-1"
                )
                doc_obj = client.get_document(document_uuid)

            self.assertEqual(doc_obj.document_data, {})

        with self.subTest(
            "index full document text if file size is lower then the max configured "
            "size."
        ):
            document_uuid = "554be64c-e6af-49b5-8af5-80e83155212d"

            doc = IndexDocumentFactory(
                uuid=document_uuid,
                inhoud="http://localhost/document/c80fcb40-f6af-44a4-90ab-07f75b47e9cb",
                bestandsomvang=800,
            )

            # verify that it's indexed
            with get_elasticsearch_client() as client:
                client.index_document(
                    doc, service="documenten-api", group_slug="group-1"
                )
                doc_obj = client.get_document(document_uuid)

            self.assertEqual(
                doc_obj.document_data[0].attachment.content,
                "Document 'c80fcb40-f6af-44a4-90ab-07f75b47e9cb'",
            )

    def test_update_full_document_text(self):
        ServiceFactory.create(for_download_url_mock_service=True)
        document_uuid = "e62db63f-9e99-41a4-88a9-be9cc3d7509a"

        doc = IndexDocumentFactory(
            uuid=document_uuid,
            inhoud="http://localhost/document/ff2c18cf-8165-45d3-873d-b68e676f99ff",
            bestandsomvang=1000,
        )

        # verify that it's indexed
        with get_elasticsearch_client() as client:
            client.index_document(doc, service="documenten-api", group_slug="group-1")
            doc_obj = client.get_document(document_uuid)

        self.assertEqual(
            doc_obj.document_data[0].attachment.content,
            "Document 'ff2c18cf-8165-45d3-873d-b68e676f99ff'",
        )

        # Update document data by changing response content from url
        doc = IndexDocumentFactory(
            uuid=document_uuid,
            inhoud="http://localhost/document/8decfefc-9879-45e8-8641-2096bbd5dba8",
            bestandsomvang=1000,
        )

        # verify that it's indexed
        with get_elasticsearch_client() as client:
            client.index_document(doc, service="documenten-api", group_slug="group-1")
            doc_obj = client.get_document(document_uuid)

        self.assertEqual(
            doc_obj.document_data[0].attachment.content,
            "Document '8decfefc-9879-45e8-8641-2096bbd5dba8'",
        )

    def test_download_zip_document(self):
        ServiceFactory.create(for_download_url_mock_service=True)
        document_uuid = "f5a98468-92ef-49a1-8dff-4a7c682347f8"

        doc = IndexDocumentFactory(
            uuid=document_uuid,
            inhoud="http://localhost/document/zip",
            bestandsomvang=1000,
        )

        # verify that it's indexed
        with get_elasticsearch_client() as client:
            client.index_document(doc, service="documenten-api", group_slug="group-1")
            doc_obj = client.get_document(document_uuid)

        self.assertEqual(len(doc_obj["document_data"]), 2)
        self.assertEqual(doc_obj.document_data[0].attachment.content, "test1")
        self.assertEqual(doc_obj.document_data[1].attachment.content, "test2")

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

        doc = IndexDocumentFactory(
            uuid=document_uuid,
            inhoud="http://localhost/document/7zip",
            bestandsomvang=1000,
        )

        # verify that it's indexed
        with get_elasticsearch_client() as client:
            client.index_document(doc, service="documenten-api", group_slug="group-1")
            doc_obj = client.get_document(document_uuid)

        self.assertEqual(len(doc_obj["document_data"]), 2)
        self.assertEqual(doc_obj.document_data[0].attachment.content, "test1")
        self.assertEqual(doc_obj.document_data[1].attachment.content, "test2")

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
        doc = IndexDocumentFactory(
            uuid=document_uuid,
            inhoud="http://localhost/document/smol7zip",
            bestandsomvang=188,
        )

        # verify that it's indexed
        with get_elasticsearch_client() as client:
            client.index_document(doc, service="documenten-api", group_slug="group-1")
            doc_obj = client.get_document(document_uuid)
        # test that only files up to 5 bytes get indexed - the second file is discarded
        self.assertEqual(len(doc_obj["document_data"]), 1)

    def test_delete_document(self):
        with get_elasticsearch_client() as client:
            # invalid cases
            self.assertFalse(client.delete_document(None))
            self.assertFalse(client.delete_document(""))
            self.assertFalse(client.delete_document("test"))
            self.assertFalse(
                client.delete_document("452635a9-228f-4cda-9bec-66310ccbb6a1")
            )  # random

            # valid case
            document_uuid = "d9fe4844-bdf8-4d66-b613-4efa71598105"
            doc = IndexDocumentFactory(uuid=document_uuid)
            client.index_document(doc, service="documenten-api", group_slug="group-1")

            self.assertIsNotNone(client.get_document(document_uuid))
            self.assertTrue(client.delete_document(document_uuid))


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class IndexAllDocumentsTaskTests(VCRMixin, ElasticSearchAPITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.documenten_service = ServiceFactory.create(
            for_drc_service_docker_compose=True
        )
        cls.zaken_service = ServiceFactory.create(for_zrc_service_docker_compose=True)
        ZGWApiGroupConfigFactory.create(
            drc_service=cls.documenten_service,
            zrc_service=cls.zaken_service,
        )

        cls.documenten_service_2 = ServiceFactory.create(
            for_drc_service_docker_compose=True
        )
        cls.zaken_service2 = ServiceFactory.create(for_zrc_service_docker_compose=True)

        ZGWApiGroupConfigFactory.create(
            drc_service=cls.documenten_service_2,
            zrc_service=cls.zaken_service2,
        )

    # TODO more tests for documents from open-zaak
    # TODO investigate why is slow without vcr
    def test_indexes_documents(self):
        index_all_documents()
        doc = None
        with get_elasticsearch_client() as client:
            total_documents = client.get_total_count(
                index="document", doc_type=Document
            )
            doc_uuid = "ea16fa8c-4bab-4065-a28a-f6574625205d"
            doc = client.get_document(doc_uuid)

        self.assertIsNotNone(doc)
        self.assertEqual(total_documents, 20)  # total documents from VCR
        self.assertEqual(doc.uuid, doc_uuid)
        self.assertEqual(doc.identificatie, "DOCUMENT-2026-0000000001")

        self.assertTrue(doc.zaak_referenties)

        if doc.zaak_referenties:
            zaak = doc.zaak_referenties[0]

            self.assertIsNotNone(zaak.url)
            self.assertIn("/zaken/", zaak.url)

            self.assertIsNotNone(zaak.identificatie)
            self.assertIsNotNone(zaak.object_type)

    def test_creatiedatum_prevents_reindexing_by_double_call(self):
        index_all_documents()
        index_all_documents()
        index_all_documents()

        doc = None
        with get_elasticsearch_client() as client:
            total_documents = client.get_total_count(
                index="document", doc_type=Document
            )
            doc_uuid = "ea16fa8c-4bab-4065-a28a-f6574625205d"
            doc = client.get_document(doc_uuid)

        self.assertIsNotNone(doc)
        self.assertEqual(total_documents, 20)  # total documents from VCR
        self.assertEqual(doc.uuid, doc_uuid)
        self.assertEqual(doc.identificatie, "DOCUMENT-2026-0000000001")

    def test_document_contains_zaak(self):
        index_all_documents()

        doc_uuid = "d34816d6-50c6-49ea-9b84-4803cbc45a3a"

        with get_elasticsearch_client() as client:
            doc = client.get_document(doc_uuid)

        self.assertIsNotNone(doc)
        self.assertTrue(doc.zaak_referenties)

        zaak = doc.zaak_referenties[0]

        self.assertIn("/zaken/", zaak.url)

        self.assertNotEqual(zaak.identificatie, "")
        self.assertIsNotNone(zaak.omschrijving)

    def test_document_contains_zaakreferentie_service_slug(self):
        index_all_documents()

        doc_uuid = "d34816d6-50c6-49ea-9b84-4803cbc45a3a"

        with get_elasticsearch_client() as client:
            doc = client.get_document(doc_uuid)

        self.assertIsNotNone(doc)
        self.assertTrue(doc.zaak_referenties)

        zaak = doc.zaak_referenties[0]

        self.assertIn("/zaken/", zaak.url)
        self.assertEqual(zaak.service_slug, "zaken-api")

        self.assertNotEqual(zaak.identificatie, "")
        self.assertIsNotNone(zaak.omschrijving)

    def test_document_without_oio_or_zaak_results_in_empty_zaak_refs(self):
        with patch(
            "opendms.api.clients.documenten.ObjectInformatieObjectClient.get_by_informatieobject",
            return_value=[],
        ):
            index_all_documents()

        with get_elasticsearch_client() as client:
            doc_uuid = "ea16fa8c-4bab-4065-a28a-f6574625205d"
            doc = client.get_document(doc_uuid)

        self.assertIsNotNone(doc)
        self.assertEqual(doc.zaak_referenties, [])

    def test_no_services_raises(self):
        ZGWApiGroupConfig.objects.all().delete()

        with self.assertRaises(ExternalServiceUnavailable):
            index_all_documents()


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class ValidateExpiredDocumentsTaskTests(VCRMixin, ElasticSearchAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.service1 = ServiceFactory.create(for_drc_service_docker_compose=True)
        ZGWApiGroupConfigFactory.create(drc_service=cls.service1)

    def test_get_expired_document(self):
        now = datetime.now(UTC)

        docs = [
            IndexDocumentFactory.build(
                uuid="expired-1",
                creatiedatum="2026-03-14",
                last_checked_at=now - timedelta(days=2),
                next_check_at=now - timedelta(days=1),  # expired
            ),
            IndexDocumentFactory.build(
                uuid="expired-2",
                creatiedatum="2026-03-15",
                last_checked_at=now - timedelta(days=1, hours=1),
                next_check_at=now - timedelta(hours=1),  # expired
            ),
            IndexDocumentFactory.build(
                uuid="valid-1",
                creatiedatum="2026-03-16",
                last_checked_at=now,
                next_check_at=now + timedelta(days=1),  # not expired
            ),
        ]

        with get_elasticsearch_client() as client:
            for doc in docs:
                client.index_document(
                    doc,
                    service="documenten-api",
                    group_slug="group-test",
                )

            expired_docs = client.get_expired_documents(now, batch_size=10)

        expired_uuids = {d["uuid"] for d in expired_docs}
        self.assertIn("expired-1", expired_uuids)
        self.assertIn("expired-2", expired_uuids)
        self.assertNotIn("valid-1", expired_uuids)

        for doc in expired_docs:
            self.assertEqual(doc["service_slug"], "documenten-api")
            self.assertEqual(doc["group_slug"], "group-test")

    @freeze_time("2026-03-30T12:00:00Z")
    def test_validate_extends_or_deletes_documents(self):
        now = datetime.now(UTC)
        extension_days = 10

        documents = [
            IndexDocumentFactory.build(
                uuid="11111111-1111-1111-1111-111111111111",
                last_checked_at=now - timedelta(days=2),
                next_check_at=now - timedelta(days=1),  # due, should be deleted
                creatiedatum="2026-03-28",
            ),
            IndexDocumentFactory.build(
                uuid="22222222-2222-2222-2222-222222222222",
                last_checked_at=now - timedelta(days=1, hours=1),
                next_check_at=now - timedelta(hours=1),  # due, should be deleted
                creatiedatum="2026-03-29",
            ),
            IndexDocumentFactory.build(
                uuid="33333333-3333-3333-3333-333333333333",
                last_checked_at=now,
                next_check_at=now + timedelta(days=5),  # not expired
                creatiedatum="2026-03-30",
            ),
            IndexDocumentFactory.build(
                uuid="44444444-4444-4444-4444-444444444444",
                last_checked_at=now,
                next_check_at=now + timedelta(days=10),  # not expired
                creatiedatum="2026-03-25",
            ),
            IndexDocumentFactory.build(
                uuid="c4a2d123-1817-4b3a-a330-67c1282b1594",
                last_checked_at=now - timedelta(days=1),
                next_check_at=now
                - timedelta(hours=2),  # expired but should be extended
                creatiedatum="2026-03-20",
            ),
        ]

        with get_elasticsearch_client() as client:
            for doc in documents:
                client.index_document(
                    doc,
                    service=self.service1.slug,
                    group_slug=self.service1.zgwset_drc_config.first().identifier,
                )

        validate_expired_documents(batch_size=10)

        with get_elasticsearch_client() as client:
            docs_after = client.get_all_documents()
            uuids_after = [d.uuid for d in docs_after.results]

            # The document should still exist and be extended
            self.assertIn("c4a2d123-1817-4b3a-a330-67c1282b1594", uuids_after)
            validated_doc = client.get_document("c4a2d123-1817-4b3a-a330-67c1282b1594")
            self.assertAlmostEqual(
                validated_doc.next_check_at,
                now + timedelta(days=extension_days),
                delta=timedelta(seconds=1),
            )
            self.assertAlmostEqual(
                validated_doc.last_checked_at,
                now,
                delta=timedelta(seconds=1),
            )

            # Non-due documents should remain unchanged
            for uuid in [
                "33333333-3333-3333-3333-333333333333",
                "44444444-4444-4444-4444-444444444444",
            ]:
                doc = client.get_document(uuid)
                self.assertGreater(doc.next_check_at, now)

            # Expired documents that are supposed to be deleted should not exist
            for uuid in [
                "11111111-1111-1111-1111-111111111111",
                "22222222-2222-2222-2222-222222222222",
            ]:
                doc = client.get_document(uuid)
                self.assertIsNone(doc)

    def test_no_documents_due(self):
        doc = IndexDocumentFactory.build(
            uuid="doc-valid",
            last_checked_at=datetime.now(UTC),
            next_check_at=datetime.now(UTC) + timedelta(days=5),
        )
        with get_elasticsearch_client() as client:
            client.index_document(doc, service="documenten-api", group_slug="group-1")
            count_before = client.get_total_count()

        validate_expired_documents()

        with get_elasticsearch_client() as client:
            count_after = client.get_total_count()

        self.assertEqual(count_before, count_after)

    @freeze_time("2026-03-30T12:00:00Z")
    def test_validate_hourly_task_simple_with_schedule(self):
        now = datetime.now(UTC)
        extension_days = 10

        docs = [
            IndexDocumentFactory.build(
                uuid="11111111-1111-1111-1111-111111111111",
                creatiedatum="2026-03-28",
                last_checked_at=now - timedelta(days=1),
                next_check_at=now - timedelta(hours=1),
            ),
            IndexDocumentFactory.build(
                uuid="22222222-2222-2222-2222-222222222222",
                last_checked_at=now - timedelta(days=1, hours=1),
                next_check_at=now - timedelta(hours=1),  # due, should be deleted
                creatiedatum="2026-03-29",
            ),
            IndexDocumentFactory.build(
                uuid="c4a2d123-1817-4b3a-a330-67c1282b1594",
                creatiedatum="2026-03-20",
                last_checked_at=now - timedelta(days=1),
                next_check_at=now - timedelta(hours=2),
            ),
        ]

        with get_elasticsearch_client() as client:
            for doc in docs:
                client.index_document(
                    doc,
                    service=self.service1.slug,
                    group_slug=self.service1.zgwset_drc_config.first().identifier,
                )

            schedule = current_app.conf.beat_schedule
            task_entry = schedule.get("validate_expired_documents")

            with self.subTest("Verify task schedule"):
                self.assertIsNotNone(task_entry)
                self.assertEqual(
                    task_entry["task"],
                    "opendms.search_index.document_task.validate_expired_documents",
                )
                from celery.schedules import crontab

                self.assertIsInstance(task_entry["schedule"], crontab)
                current_app.tasks[task_entry["task"]].apply()

            with self.subTest("Check extended and deleted documents"):
                with get_elasticsearch_client() as client:
                    extended = client.get_document(
                        "c4a2d123-1817-4b3a-a330-67c1282b1594"
                    )
                    self.assertIsNotNone(extended)
                    self.assertAlmostEqual(
                        extended.next_check_at,
                        now + timedelta(days=extension_days),
                        delta=timedelta(seconds=1),
                    )
                    self.assertAlmostEqual(
                        extended.last_checked_at,
                        now,
                        delta=timedelta(seconds=1),
                    )

                    deleted = client.get_document(
                        "11111111-1111-1111-1111-111111111111"
                    )
                    self.assertIsNone(deleted)

    def test_no_services_raises_exception(self):
        ZGWApiGroupConfig.objects.all().delete()

        with self.assertRaises(ExternalServiceUnavailable):
            validate_expired_documents(batch_size=10)
