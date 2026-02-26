from datetime import UTC, datetime
from unittest.mock import patch
from uuid import uuid4

from django.test import override_settings
from django.utils.translation import gettext_lazy as _

from rest_framework import status
from vng_api_common.tests import get_validation_errors, reverse

from opendms.search_index.client import get_client
from opendms.search_index.tests.base import ElasticSearchAPITestCase
from opendms.utils.tests.vcr import VCRMixin

from ..index import Document
from .factories import IndexDocumentFactory


class DocumentAPITests(ElasticSearchAPITestCase):
    url = reverse("api:document-list")

    @patch("opendms.search_index.api.viewsets.index_document.delay")
    def test_document_api_happy_flow(self, patched_index_document):
        data = IndexDocumentFactory.build(
            uuid="0c5730c7-17ed-42a7-bc3b-5ee527ef3326",
            titel="test document",
            inhoud="https://www.example.com/downloads/1",
            begin_registratie=datetime(2025, 2, 4, 0, 0, 0, tzinfo=UTC),
            bestandsomvang=3124,
        )

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        # Snake-case keys match the ES model
        snake_case_data = data.copy()
        patched_index_document.assert_called_once_with(**snake_case_data)

    def test_document_api_with_inhoud_and_without_bestandsomvang_result_in_error(self):
        data = IndexDocumentFactory.build(inhoud="https://www.example.com/downloads/1")
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        error = get_validation_errors(response, "bestandsomvang")
        self.assertEqual(error["reason"], _("Field is required when using `inhoud`."))

    @patch("opendms.search_index.api.viewsets.index_document.delay")
    def test_document_api_with_errors_does_not_call_index_document_celery_task(
        self, patched_index_document
    ):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        patched_index_document.assert_not_called()


class RemoveDocumentFromIndexAPITests(ElasticSearchAPITestCase):
    @patch("opendms.search_index.api.viewsets.remove_document_from_index.delay")
    def test_remove_document_from_index(self, patched_remove_document):
        patched_remove_document.return_value.id = "my-task-id"
        document_id = str(uuid4())
        endpoint = reverse("api:document-detail", kwargs={"uuid": document_id})

        response = self.client.delete(endpoint)
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.json()["taskId"], "my-task-id")
        patched_remove_document.assert_called_once_with(uuid=document_id)


class DocumentApiE2ETest(VCRMixin, ElasticSearchAPITestCase):
    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_document_creation_happy_flow(self):
        url = reverse("api:document-list")
        data = IndexDocumentFactory.build(
            uuid="0c5730c7-17ed-42a7-bc3b-5ee527ef3326",
            inhoud="https://www.example.com/downloads/1",
            bestandsomvang=3124,
        )

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        # verify indexed
        with get_client() as client:
            doc = Document.get(using=client, id=data["uuid"])
        self.assertIsNotNone(doc, "Expected doc to be indexed")
