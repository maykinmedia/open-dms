from datetime import date

from django.test import override_settings

from maykin_common.vcr import VCRMixin

from opendms.api.models import ZGWApiGroupConfig
from opendms.api.tests.factories import ServiceFactory, ZGWApiGroupConfigFactory
from opendms.api.utils.exceptions import ExternalServiceUnavailable

from ..client import get_elasticsearch_client
from ..index import Zaak
from ..zaak_task import index_all_zaken
from .base import ElasticSearchAPITestCase
from .factories import IndexZaakFactory


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class IndexAllZakenTaskTests(VCRMixin, ElasticSearchAPITestCase):
    zaak_uuid = "0095704d-4216-4de3-83d2-20dba551b0dc"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.zaken_service = ServiceFactory.create(for_zrc_service_docker_compose=True)
        cls.zaken_service2 = ServiceFactory.create(for_zrc_service_docker_compose=True)

        ZGWApiGroupConfigFactory.create(zrc_service=cls.zaken_service)
        ZGWApiGroupConfigFactory.create(zrc_service=cls.zaken_service2)

    def test_index_zaak_roundtrip(self):
        """Ensure a single Zaak can be indexed and retrieved."""
        zaak_data = IndexZaakFactory(
            uuid=self.zaak_uuid,
            identificatie="ZA-2026-0001",
            omschrijving="Test Zaak",
            startdatum=date(2026, 1, 1),
            registratiedatum="2026-04-07T09:00:00Z",
            url="http://localhost/zaken/1",
        )

        with get_elasticsearch_client() as client:
            obj = Zaak(**zaak_data)
            client.index_zaken(obj)
            zaak = client.get_zaak(self.zaak_uuid)

        self.assertIsNotNone(zaak)
        self.assertEqual(zaak.identificatie, "ZA-2026-0001")
        self.assertEqual(zaak.omschrijving, "Test Zaak")
        self.assertEqual(zaak.url, "http://localhost/zaken/1")

    def test_indexes_zaken_task(self):
        index_all_zaken()

        with get_elasticsearch_client() as client:
            total = client.get_total_count(index="zaak", doc_type=Zaak)
            self.assertEqual(total, 20)

            # Check one zaak
            zaak = client.get_zaak("85169f14-b860-4590-8787-4e026f90703e")
            self.assertIsNotNone(zaak)
            self.assertEqual(zaak.omschrijving, "verklaring van vernietiging")

    def test_registratiedatum_prevents_double_indexing(self):
        index_all_zaken()
        index_all_zaken()
        index_all_zaken()

        with get_elasticsearch_client() as client:
            total = client.get_total_count(index="zaak", doc_type=Zaak)
            self.assertEqual(total, 20)

    def test_no_services_raises(self):
        ZGWApiGroupConfig.objects.all().delete()

        with self.assertRaises(ExternalServiceUnavailable):
            index_all_zaken()
