import factory
from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.test.factories import ServiceFactory as _ServiceFactory

from ..models import ZGWApiGroupConfig


class ServiceFactory(_ServiceFactory):
    class Params:
        for_download_url_mock_service = factory.Trait(
            label="download-url-mock",
            api_root="http://localhost/",
            api_type=APITypes.orc,
            auth_type=AuthTypes.api_key,
            header_key="Authorization",
            header_value="Token insecure",
        )
        # See the docker compose fixtures for base URLs authentication values:
        for_zrc_service_docker_compose = factory.Trait(
            slug="zaken-api",
            label="Zaken API test",
            api_root="http://localhost:8003/zaken/api/v1/",
            api_type=APITypes.zrc,
            auth_type=AuthTypes.zgw,
            client_id="test_client_id",
            secret="test_secret_key",
        )
        for_drc_service_docker_compose = factory.Trait(
            slug="documenten-api",
            label="Documenten API test",
            api_root="http://localhost:8003/documenten/api/v1/",
            api_type=APITypes.drc,
            auth_type=AuthTypes.zgw,
            client_id="test_client_id",
            secret="test_secret_key",
        )
        for_ztc_service_docker_compose = factory.Trait(
            slug="catalogi-api",
            label="Catalogi API test",
            api_root="http://localhost:8003/catalogi/api/v1/",
            api_type=APITypes.ztc,
            auth_type=AuthTypes.zgw,
            client_id="test_client_id",
            secret="test_secret_key",
        )


class ZGWApiGroupConfigFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: f"ZGW API set {n:03d}")
    identifier = factory.Sequence(lambda n: f"zgw-api-group-{n}")
    zrc_service = factory.SubFactory(
        "zgw_consumers.test.factories.ServiceFactory", api_type=APITypes.zrc
    )
    drc_service = factory.SubFactory(
        "zgw_consumers.test.factories.ServiceFactory", api_type=APITypes.drc
    )
    ztc_service = factory.SubFactory(
        "zgw_consumers.test.factories.ServiceFactory", api_type=APITypes.ztc
    )

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = ZGWApiGroupConfig
