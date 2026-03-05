from functools import partial

from django.core.cache import cache

from zgw_consumers.client import build_client
from zgw_consumers.models import Service
from zgw_consumers.nlx import NLXClient
from zgw_consumers.service import pagination_helper

from ..utils.exceptions import NoServiceConfigured
from ..utils.validators import extract_uuid
from .typing import ZaakTypeAPI


class ZaakTypeClient(NLXClient):
    """
    Client for retrieving Zaaktypen from a ZTC service.
    """

    endpoint = "zaaktypen"

    def get_items(self, params: dict) -> list[ZaakTypeAPI]:
        response = self.get(self.endpoint, params=params)
        response.raise_for_status()
        data = response.json()
        return [
            ZaakTypeAPI(
                uuid=extract_uuid(record["url"]),
                catalogus=record["catalogus"],
                identificatie=record["identificatie"],
                omschrijving=record["omschrijving"],
                beginGeldigheid=record["beginGeldigheid"],
                eindeGeldigheid=record["eindeGeldigheid"],
            )
            for record in pagination_helper(self, data)
        ]

    def get_item_by_uuid(self, uuid: str) -> ZaakTypeAPI | None:
        response = self.get(f"{self.endpoint}/{uuid}")
        data = response.json()
        response.raise_for_status()

        return ZaakTypeAPI(
            uuid=extract_uuid(data["url"]),
            catalogus=data["catalogus"],
            identificatie=data["identificatie"],
            omschrijving=data["omschrijving"],
            beginGeldigheid=data["beginGeldigheid"],
            eindeGeldigheid=data["eindeGeldigheid"],
        )

    def get_cached_items(
        self, service_slug: str, params: dict, cache_timeout: int = 300
    ) -> list[ZaakTypeAPI]:

        if params:
            return self.get_items(params)

        return cache.get_or_set(
            key=f"zaaktypen:{service_slug}:",
            default=partial(self.get_items, params),
            timeout=cache_timeout,
        )


def get_zaaktypen_client(service: Service) -> ZaakTypeClient:
    if service is None:
        raise NoServiceConfigured("No ZaakTypen API service configured!")

    return build_client(service, client_factory=ZaakTypeClient)
