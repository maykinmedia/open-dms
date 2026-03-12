from functools import partial

from django.core.cache import cache

from zgw_consumers.client import build_client
from zgw_consumers.models import Service
from zgw_consumers.nlx import NLXClient
from zgw_consumers.service import pagination_helper

from ..typing import ZaakTypeAPI
from ..utils.mixins import HttpRequestMixin
from ..utils.validators import extract_uuid


class ZaakTypeClient(HttpRequestMixin, NLXClient):
    """
    Client for retrieving Zaaktypen from a ZTC service.
    """

    endpoint = "zaaktypen"

    def get_items(self, params: dict) -> list[ZaakTypeAPI]:
        data = self.make_request(self.endpoint, params)
        return [
            ZaakTypeAPI(
                uuid=extract_uuid(record["url"]),
                url=record["url"],
                catalogus=record["catalogus"],
                identificatie=record["identificatie"],
                omschrijving=record["omschrijving"],
                beginGeldigheid=record["beginGeldigheid"],
                eindeGeldigheid=record["eindeGeldigheid"],
            )
            for record in pagination_helper(self, data)
        ]

    def get_item_by_uuid(self, uuid: str) -> ZaakTypeAPI | None:
        data = self.make_request(f"{self.endpoint}/{uuid}")
        return ZaakTypeAPI(
            uuid=extract_uuid(data["url"]),
            url=data["url"],
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
    return build_client(service, client_factory=ZaakTypeClient)
