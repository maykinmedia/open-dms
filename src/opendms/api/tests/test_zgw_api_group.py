from django.db import IntegrityError
from django.test import TestCase

from zgw_consumers.constants import APITypes
from zgw_consumers.models import Service

from opendms.api.models import ZGWApiGroupConfig
from opendms.api.tests.factories import ServiceFactory


class ZGWApiConfigurationStepTests(TestCase):
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.zaken_service = ServiceFactory.create(
            for_zrc_service_docker_compose=True,
        )
        cls.documenten_service = ServiceFactory.create(
            for_drc_service_docker_compose=True,
        )
        cls.catalogi_service = ServiceFactory.create(
            for_ztc_service_docker_compose=True,
        )

    def test_create_success(self):
        self.assertFalse(ZGWApiGroupConfig.objects.exists())

        ZGWApiGroupConfig.objects.create(
            name="Config 1",
            identifier="config-1",
            zrc_service=self.zaken_service,
            ztc_service=self.catalogi_service,
            drc_service=self.documenten_service,
        )

        config1 = ZGWApiGroupConfig.objects.get()

        self.assertEqual(config1.name, "Config 1")
        self.assertEqual(config1.identifier, "config-1")
        self.assertEqual(config1.zrc_service, self.zaken_service)
        self.assertEqual(config1.drc_service, self.documenten_service)
        self.assertEqual(config1.ztc_service, self.catalogi_service)

    def test_update_existing_config(self):
        ZGWApiGroupConfig.objects.create(
            name="Config 1",
            identifier="config-1",
            zrc_service=self.zaken_service,
            ztc_service=self.catalogi_service,
            drc_service=self.documenten_service,
        )

        config = ZGWApiGroupConfig.objects.get()

        config.name = "test"
        config.drc_service = ServiceFactory.create(
            api_type=APITypes.drc, slug="drc-test"
        )
        config.save()

        config = ZGWApiGroupConfig.objects.get()

        self.assertEqual(config.name, "test")
        self.assertEqual(config.identifier, "config-1")
        self.assertEqual(config.drc_service, Service.objects.get(slug="drc-test"))

    def test_invalid_unique_ztc_service(self):
        ZGWApiGroupConfig.objects.create(
            name="Config 1",
            identifier="config-1",
            zrc_service=self.zaken_service,
            ztc_service=self.catalogi_service,
            drc_service=self.documenten_service,
        )

        with self.assertRaises(IntegrityError) as error:
            ZGWApiGroupConfig.objects.create(
                name="Config 2",
                identifier="config-2",
                zrc_service=ServiceFactory.create(
                    api_type=APITypes.zrc, slug="zrc-test"
                ),
                ztc_service=self.catalogi_service,
                drc_service=ServiceFactory.create(
                    api_type=APITypes.drc, slug="drc-test"
                ),
            )
        self.assertIn(
            "duplicate key value violates unique constraint", str(error.exception)
        )

    def test_valid_unique_ztc_service(self):
        ZGWApiGroupConfig.objects.create(
            name="Config 1",
            identifier="config-1",
            zrc_service=self.zaken_service,
            ztc_service=self.catalogi_service,
            drc_service=self.documenten_service,
        )

        ZGWApiGroupConfig.objects.create(
            name="Config 2",
            identifier="config-2",
            zrc_service=self.zaken_service,
            ztc_service=ServiceFactory.create(
                api_type=APITypes.ztc,
                slug="ztc-test-1",
                api_root="http://testserver:8003/catalogi/api/v1/",
            ),
            drc_service=self.documenten_service,
        )
