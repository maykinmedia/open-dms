from pathlib import Path

from django.db import IntegrityError
from django.test import TestCase

from django_setup_configuration.test_utils import execute_single_step
from zgw_consumers.models import Service

from opendms.api.models import ZGWApiGroupConfig
from opendms.api.setup_configuration.steps import ZGWApiConfigurationStep
from opendms.api.tests.factories import ServiceFactory, ZGWApiGroupConfigFactory

TEST_FILES = (Path(__file__).parent / "files").resolve()
CONFIG_FILE_PATH = str(TEST_FILES / "setup_config.yaml")
CONFIG_FILE_PATH_ALL_FIELDS = str(TEST_FILES / "setup_config_all_fields.yaml")
CONFIG_FILE_DUPLICATED_ZTC_PATH = str(TEST_FILES / "setup_config_duplicate_ztc.yaml")


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

    def test_execute_success(self):
        execute_single_step(ZGWApiConfigurationStep, yaml_source=CONFIG_FILE_PATH)

        self.assertEqual(ZGWApiGroupConfig.objects.count(), 1)

        config1 = ZGWApiGroupConfig.objects.get()

        self.assertEqual(config1.name, "Config 1")
        self.assertEqual(config1.identifier, "config-1")
        self.assertEqual(config1.zrc_service, self.zaken_service)
        self.assertEqual(config1.drc_service, self.documenten_service)
        self.assertEqual(config1.ztc_service, self.catalogi_service)

    def test_execute_update_existing_config(self):
        ZGWApiGroupConfigFactory.create(name="old name", identifier="config-1")

        execute_single_step(ZGWApiConfigurationStep, yaml_source=CONFIG_FILE_PATH)

        self.assertEqual(ZGWApiGroupConfig.objects.count(), 1)

        config1 = ZGWApiGroupConfig.objects.get()

        self.assertEqual(config1.name, "Config 1")
        self.assertEqual(config1.identifier, "config-1")

    def test_execute_with_required_fields(self):
        execute_single_step(
            ZGWApiConfigurationStep, yaml_source=CONFIG_FILE_PATH_ALL_FIELDS
        )

        self.assertEqual(ZGWApiGroupConfig.objects.count(), 1)

        config = ZGWApiGroupConfig.objects.get()

        self.assertEqual(config.name, "Config 1")
        self.assertEqual(config.identifier, "config-1")
        self.assertEqual(config.zrc_service, self.zaken_service)
        self.assertEqual(config.drc_service, self.documenten_service)
        self.assertEqual(config.ztc_service, self.catalogi_service)

    def test_execute_is_idempotent(self):
        self.assertFalse(ZGWApiGroupConfig.objects.exists())

        with self.subTest("run step first time"):
            execute_single_step(
                ZGWApiConfigurationStep, yaml_source=CONFIG_FILE_PATH_ALL_FIELDS
            )

            self.assertEqual(ZGWApiGroupConfig.objects.count(), 1)

        with self.subTest("run step second time"):
            execute_single_step(
                ZGWApiConfigurationStep, yaml_source=CONFIG_FILE_PATH_ALL_FIELDS
            )

            # no additional configs created, but existing one updated
            self.assertEqual(ZGWApiGroupConfig.objects.count(), 1)

    def test_execute_service_not_found_raises_error(self):
        self.zaken_service.slug = "test"
        self.zaken_service.save()

        with self.assertRaisesMessage(
            Service.DoesNotExist,
            "Service matching query does not exist. (identifier = zaken-api)",
        ):
            execute_single_step(
                ZGWApiConfigurationStep, yaml_source=CONFIG_FILE_PATH_ALL_FIELDS
            )

        self.assertEqual(ZGWApiGroupConfig.objects.count(), 0)

    def test_execute_ztc_unique_service_raises_error(self):
        ZGWApiGroupConfigFactory.create(
            zrc_service=self.zaken_service,
            ztc_service=self.catalogi_service,
            drc_service=self.documenten_service,
        )
        config = ZGWApiGroupConfig.objects.get()
        self.assertEqual(config.ztc_service.slug, "catalogi-api")

        with self.assertRaises(IntegrityError) as error:
            execute_single_step(ZGWApiConfigurationStep, yaml_source=CONFIG_FILE_PATH)

        self.assertIn(
            "duplicate key value violates unique constraint", str(error.exception)
        )

    def test_execute_ztc_unique_service_config_file_raises_error(self):
        self.assertEqual(ZGWApiGroupConfig.objects.count(), 0)

        with self.assertRaises(IntegrityError) as error:
            execute_single_step(
                ZGWApiConfigurationStep, yaml_source=CONFIG_FILE_DUPLICATED_ZTC_PATH
            )
        self.assertIn(
            "duplicate key value violates unique constraint", str(error.exception)
        )
        self.assertEqual(ZGWApiGroupConfig.objects.count(), 0)
