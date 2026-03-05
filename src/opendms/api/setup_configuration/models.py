from django_setup_configuration.fields import DjangoModelRef
from django_setup_configuration.models import ConfigurationModel
from pydantic import Field

from ..models import ZGWApiGroupConfig


class SingleZGWApiGroupConfigModel(ConfigurationModel):
    zaken_service_identifier: str = DjangoModelRef(
        ZGWApiGroupConfig,
        "zrc_service",
    )
    documenten_service_identifier: str = DjangoModelRef(
        ZGWApiGroupConfig,
        "drc_service",
    )
    catalogi_service_identifier: str = DjangoModelRef(
        ZGWApiGroupConfig,
        "ztc_service",
    )

    class Meta:
        django_model_refs = {ZGWApiGroupConfig: ["name", "identifier"]}
        extra_kwargs = {
            "identifier": {"examples": ["open-zaak-acceptance"]},
            "name": {"examples": ["Open Zaak acceptance environment"]},
        }


class ZGWApiGroupConfigModel(ConfigurationModel):
    groups: list[SingleZGWApiGroupConfigModel] = Field()
