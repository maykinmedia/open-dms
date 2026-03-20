from maykin_common.vcr import VCRMixin

from ..client import get_elasticsearch_client
from ..ingest import setup_document_attachment_processor
from .base import ElasticSearchTestCase


class IngestPipelineTest(VCRMixin, ElasticSearchTestCase):
    def test_document_attachment_processor_with_correct_client(self):
        with get_elasticsearch_client() as es_client:
            success = setup_document_attachment_processor(client=es_client.client)

        self.assertTrue(success)
