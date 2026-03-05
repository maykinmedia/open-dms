from pathlib import Path

from django.test import TestCase

from django_setup_configuration.test_utils import execute_single_step
from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.models import Service
from zgw_consumers.test.factories import ServiceFactory

from opendms.api.models import ZGWApiGroupConfig
from opendms.api.setup_configuration.steps import ZGWApiConfigurationStep
from opendms.api.tests.factories import ZGWApiGroupConfigFactory

TEST_FILES = (Path(__file__).parent / "files").resolve()
CONFIG_FILE_PATH = str(TEST_FILES / "setup_config.yaml")
CONFIG_FILE_PATH_ALL_FIELDS = str(TEST_FILES / "setup_config_all_fields.yaml")


class ZGWApiConfigurationStepTests(TestCase):
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.zaken_service = ServiceFactory.create(
            slug="zaken-api",
            label="Zaken API test",
            api_root="http://localhost:8003/zaken/api/v1/",
            api_type=APITypes.zrc,
            auth_type=AuthTypes.zgw,
            client_id="test_client_id",
            secret="test_secret_key",
        )
        cls.documenten_service = ServiceFactory.create(
            slug="documenten-api",
            label="Documenten API test",
            api_root="http://localhost:8003/documenten/api/v1/",
            api_type=APITypes.drc,
            auth_type=AuthTypes.zgw,
            client_id="test_client_id",
            secret="test_secret_key",
        )
        cls.catalogi_service = ServiceFactory.create(
            slug="catalogi-api",
            label="Catalogi API test",
            api_root="http://localhost:8003/catalogi/api/v1/",
            api_type=APITypes.ztc,
            auth_type=AuthTypes.zgw,
            client_id="test_client_id",
            secret="test_secret_key",
        )

    def test_execute_success(self):
        execute_single_step(ZGWApiConfigurationStep, yaml_source=CONFIG_FILE_PATH)

        self.assertEqual(ZGWApiGroupConfig.objects.count(), 2)

        config1, config2 = ZGWApiGroupConfig.objects.order_by("pk")

        self.assertEqual(config1.name, "Config 1")
        self.assertEqual(config1.identifier, "config-1")
        self.assertEqual(config1.zrc_service, self.zaken_service)
        self.assertEqual(config1.drc_service, self.documenten_service)
        self.assertEqual(config1.ztc_service, self.catalogi_service)

        self.assertEqual(config2.name, "Config 2")
        self.assertEqual(config2.identifier, "config-2")
        self.assertEqual(config2.zrc_service, self.zaken_service)
        self.assertEqual(config2.drc_service, self.documenten_service)
        self.assertEqual(config2.ztc_service, self.catalogi_service)

    def test_execute_update_existing_config(self):
        ZGWApiGroupConfigFactory.create(name="old name", identifier="config-1")

        execute_single_step(ZGWApiConfigurationStep, yaml_source=CONFIG_FILE_PATH)

        self.assertEqual(ZGWApiGroupConfig.objects.count(), 2)

        config1, config2 = ZGWApiGroupConfig.objects.order_by("pk")

        self.assertEqual(config1.name, "Config 1")
        self.assertEqual(config1.identifier, "config-1")

        self.assertEqual(config2.name, "Config 2")
        self.assertEqual(config2.identifier, "config-2")

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
