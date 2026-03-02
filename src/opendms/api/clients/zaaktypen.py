from typing import TypedDict
from uuid import UUID

from django.core.cache import cache

from zgw_consumers.client import build_client
from zgw_consumers.models import Service
from zgw_consumers.nlx import NLXClient
from zgw_consumers.service import pagination_helper

from ..utils.exceptions import NoServiceConfigured
from ..utils.validators import extract_uuid


class ZaakTypeAPI(TypedDict):
    uuid: UUID
    catalogus: str
    identificatie: str
    omschrijving: str


class ZaakTypeClient(NLXClient):
    """
    Client for retrieving Zaaktypen from a ZTC service.
    """

    endpoint = "zaaktypen"

    def get_items(self) -> list[ZaakTypeAPI]:
        response = self.get(self.endpoint)
        response.raise_for_status()
        data = response.json()

        return [
            ZaakTypeAPI(
                uuid=extract_uuid(record["url"]),
                catalogus=record["catalogus"],
                identificatie=record["identificatie"],
                omschrijving=record["omschrijving"],
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
        )

    def get_cached_items(
        self, service_slug: str, cache_timeout: int = 300
    ) -> list[ZaakTypeAPI]:
        cache_key = f"zaaktypen:{service_slug}"
        items: list[ZaakTypeAPI] | None = cache.get(cache_key)

        if items is None:
            items = self.get_items()
            cache.set(cache_key, items, cache_timeout)
        return items


def get_zaaktypen_client(service: Service) -> ZaakTypeClient:
    if service is None:
        raise NoServiceConfigured("No ZaakTypen API service configured!")

    return build_client(service, client_factory=ZaakTypeClient)
