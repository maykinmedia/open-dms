from functools import partial

from django.core.cache import cache

from zgw_consumers.client import build_client
from zgw_consumers.models import Service
from zgw_consumers.nlx import NLXClient
from zgw_consumers.service import pagination_helper

from ..utils.exceptions import NoServiceConfigured
from ..utils.validators import extract_uuid
from .typing import ZaakAPI


class ZaakClient(NLXClient):
    """
    Client for retrieving Zaken from a ZTC service.
    """

    endpoint = "zaaktypen"

    def get_items(self, params: dict) -> list[ZaakAPI]:
        response = self.get(self.endpoint, params=params)
        response.raise_for_status()
        data = response.json()
        return [
            ZaakAPI(
                uuid=extract_uuid(record["url"]),
                identificatie=record["identificatie"],
            )
            for record in pagination_helper(self, data)
        ]

    def get_item_by_uuid(self, uuid: str) -> ZaakAPI | None:
        response = self.get(f"{self.endpoint}/{uuid}")
        data = response.json()
        response.raise_for_status()

        return ZaakAPI(
            uuid=extract_uuid(data["url"]),
            identificatie=data["identificatie"],
        )

    def get_cached_items(
        self, service_slug: str, params: dict, cache_timeout: int = 300
    ) -> list[ZaakAPI]:

        if params:
            return self.get_items(params)

        return cache.get_or_set(
            key=f"zaaktypen:{service_slug}:zaken",
            default=partial(self.get_items, params),
            timeout=cache_timeout,
        )


def get_zaken_client(service: Service) -> ZaakClient:
    if service is None:
        raise NoServiceConfigured("No ZaakTypen API service configured!")

    return build_client(service, client_factory=ZaakClient)
