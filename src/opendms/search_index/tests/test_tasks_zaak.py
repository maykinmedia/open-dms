from datetime import date, timedelta

from django.test import override_settings
from django.utils import timezone

from celery import current_app
from freezegun import freeze_time
from maykin_common.vcr import VCRMixin

from opendms.api.models import ZGWApiGroupConfig
from opendms.api.tests.factories import ServiceFactory, ZGWApiGroupConfigFactory
from opendms.api.utils.exceptions import ExternalServiceUnavailable

from ..client import get_elasticsearch_client
from ..index import Zaak
from ..zaak_task import index_all_zaken, validate_expired_zaken
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
        cls.zaaktype_service = ServiceFactory.create(
            for_ztc_service_docker_compose=True
        )

        ZGWApiGroupConfigFactory.create(
            zrc_service=cls.zaken_service, ztc_service=cls.zaaktype_service
        )
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
            client.index_zaken(obj, service_slug="zaken-api", group_slug="group-1")
            zaak = client.get_zaak(self.zaak_uuid)

        self.assertIsNotNone(zaak)
        self.assertEqual(zaak.identificatie, "ZA-2026-0001")
        self.assertEqual(zaak.omschrijving, "Test Zaak")
        self.assertEqual(zaak.url, "http://localhost/zaken/1")
        self.assertEqual(zaak.ztc_service_slug, "catalogi-api")

    def test_indexes_zaken_task(self):
        index_all_zaken()

        with get_elasticsearch_client() as client:
            total = client.get_total_count(index="zaak", doc_type=Zaak)
            self.assertEqual(total, 20)

            # Check one zaak
            zaak = client.get_zaak("85169f14-b860-4590-8787-4e026f90703e")
            self.assertIsNotNone(zaak)
            self.assertEqual(zaak.omschrijving, "verklaring van vernietiging")
            self.assertIsNotNone(zaak.ztc_service_slug)
            self.assertIsNotNone(zaak.startjaar)
            self.assertIsNotNone(zaak.ztc_uuid)

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


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class ValidateExpiredZakenTaskTests(VCRMixin, ElasticSearchAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.service1 = ServiceFactory.create(for_zrc_service_docker_compose=True)
        ZGWApiGroupConfigFactory.create(zrc_service=cls.service1)

    def test_get_expired_zaken(self):
        now = timezone.now()

        zaken = [
            IndexZaakFactory.build(
                uuid="expired-1",
                registratiedatum="2026-03-14",
                last_checked_at=now - timedelta(days=2),
                next_check_at=now - timedelta(days=1),  # expired
            ),
            IndexZaakFactory.build(
                uuid="expired-2",
                registratiedatum="2026-03-15",
                last_checked_at=now - timedelta(days=1, hours=1),
                next_check_at=now - timedelta(hours=1),  # expired
            ),
            IndexZaakFactory.build(
                uuid="valid-1",
                registratiedatum="2026-03-16",
                last_checked_at=now,
                next_check_at=now + timedelta(days=1),  # not expired
            ),
        ]

        with get_elasticsearch_client() as client:
            for zaak in zaken:
                client.index_zaken(
                    zaak,
                    service_slug="zaken-api",
                    group_slug="group-test",
                )

            expired_zaken = client.get_expired_zaken(now, batch_size=10)

        expired_uuids = {d["uuid"] for d in expired_zaken}
        self.assertIn("expired-1", expired_uuids)
        self.assertIn("expired-2", expired_uuids)
        self.assertNotIn("valid-1", expired_uuids)

        for zaak in expired_zaken:
            self.assertEqual(zaak["service_slug"], "zaken-api")
            self.assertEqual(zaak["group_slug"], "group-test")

    @freeze_time("2026-03-30T12:00:00Z")
    def test_validate_extends_or_deletes_zaken(self):
        now = timezone.now()
        extension_days = 10

        zaken = [
            IndexZaakFactory.build(
                uuid="11111111-1111-1111-1111-111111111111",
                last_checked_at=now - timedelta(days=2),
                next_check_at=now - timedelta(days=1),  # due, should be deleted
                registratiedatum="2026-03-28",
            ),
            IndexZaakFactory.build(
                uuid="22222222-2222-2222-2222-222222222222",
                last_checked_at=now - timedelta(days=1, hours=1),
                next_check_at=now - timedelta(hours=1),  # due, should be deleted
                registratiedatum="2026-03-29",
            ),
            IndexZaakFactory.build(
                uuid="33333333-3333-3333-3333-333333333333",
                last_checked_at=now,
                next_check_at=now + timedelta(days=5),  # not expired
                registratiedatum="2026-03-30",
            ),
            IndexZaakFactory.build(
                uuid="44444444-4444-4444-4444-444444444444",
                last_checked_at=now,
                next_check_at=now + timedelta(days=10),  # not expired
                registratiedatum="2026-03-25",
            ),
            IndexZaakFactory.build(
                uuid="85169f14-b860-4590-8787-4e026f90703e",
                last_checked_at=now - timedelta(days=1),
                next_check_at=now
                - timedelta(hours=2),  # expired but should be extended
                registratiedatum="2026-03-20",
            ),
        ]

        with get_elasticsearch_client() as client:
            for zaak in zaken:
                client.index_zaken(
                    zaak,
                    service_slug="zaken-api",
                    group_slug="group-test",
                )

        validate_expired_zaken(batch_size=10)

        with get_elasticsearch_client() as client:
            zaak_after = client.get_all_zaken()
            uuids_after = [d.uuid for d in zaak_after.results]

            # The zaak should still exist and be extended
            self.assertIn("85169f14-b860-4590-8787-4e026f90703e", uuids_after)
            validated_zaak = client.get_zaak("85169f14-b860-4590-8787-4e026f90703e")
            self.assertAlmostEqual(
                validated_zaak.next_check_at,
                now + timedelta(days=extension_days),
                delta=timedelta(seconds=1),
            )
            self.assertAlmostEqual(
                validated_zaak.last_checked_at,
                now,
                delta=timedelta(seconds=1),
            )

            # Non-due zaken should remain unchanged
            for uuid in [
                "33333333-3333-3333-3333-333333333333",
                "44444444-4444-4444-4444-444444444444",
            ]:
                zaak = client.get_zaak(uuid)
                self.assertGreater(zaak.next_check_at, now)

            # Expired zaken that are supposed to be deleted should not exist
            for uuid in [
                "11111111-1111-1111-1111-111111111111",
                "22222222-2222-2222-2222-222222222222",
            ]:
                doc = client.get_zaak(uuid)
                self.assertIsNone(doc)

    def test_no_zaken_due(self):
        doc = IndexZaakFactory.build(
            uuid="zaak-valid",
            last_checked_at=timezone.now(),
            next_check_at=timezone.now() + timedelta(days=5),
        )
        with get_elasticsearch_client() as client:
            client.index_zaken(doc, service_slug="zaken-api", group_slug="group-1")
            count_before = client.get_total_count(index="zaak", doc_type=Zaak)

        validate_expired_zaken()

        with get_elasticsearch_client() as client:
            count_after = client.get_total_count(index="zaak", doc_type=Zaak)

        self.assertEqual(count_before, count_after)

    @freeze_time("2026-03-30T12:00:00Z")
    def test_validate_hourly_task_simple_with_schedule(self):
        now = timezone.now()
        extension_days = 10

        docs = [
            IndexZaakFactory.build(
                uuid="11111111-1111-1111-1111-111111111111",
                registratiedatum="2026-03-28",
                last_checked_at=now - timedelta(days=1),
                next_check_at=now - timedelta(hours=1),
            ),
            IndexZaakFactory.build(
                uuid="22222222-2222-2222-2222-222222222222",
                registratiedatum="2026-03-29",
                last_checked_at=now - timedelta(days=1, hours=1),
                next_check_at=now - timedelta(hours=1),  # due, should be deleted
            ),
            IndexZaakFactory.build(
                uuid="85169f14-b860-4590-8787-4e026f90703e",
                registratiedatum="2026-03-20",
                last_checked_at=now - timedelta(days=1),
                next_check_at=now - timedelta(hours=2),
            ),
        ]

        with get_elasticsearch_client() as client:
            for doc in docs:
                client.index_zaken(
                    doc,
                    service_slug=self.service1.slug,
                    group_slug=self.service1.zgwset_zrc_config.first().identifier,
                )

            schedule = current_app.conf.beat_schedule
            task_entry = schedule.get("validate_expired_zaken")

            with self.subTest("Verify task schedule"):
                self.assertIsNotNone(task_entry)
                self.assertEqual(
                    task_entry["task"],
                    "opendms.search_index.zaak_task.validate_expired_zaken",
                )
                from celery.schedules import crontab

                self.assertIsInstance(task_entry["schedule"], crontab)
                current_app.tasks[task_entry["task"]].apply()

            with self.subTest("Check extended and deleted zaken"):
                with get_elasticsearch_client() as client:
                    extended = client.get_zaak("85169f14-b860-4590-8787-4e026f90703e")
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

                    deleted = client.get_zaak("11111111-1111-1111-1111-111111111111")
                    self.assertIsNone(deleted)

    def test_no_services_raises_exception(self):
        ZGWApiGroupConfig.objects.all().delete()

        with self.assertRaises(ExternalServiceUnavailable):
            validate_expired_zaken(batch_size=10)
