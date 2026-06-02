from functools import partial
from typing import NoReturn

from django.core.cache import cache

from zgw_consumers.client import build_client
from zgw_consumers.models import Service
from zgw_consumers.nlx import NLXClient

from ..typing import ZaakType, ZaakTypenPaginatedResponse
from ..utils.mixins import HttpRequestMixin
from ..utils.validators import extract_uuid


class ZaakTypeClient(HttpRequestMixin, NLXClient):
    """
    Client for retrieving Zaaktypen from a ZTC service.
    """

    endpoint = "zaaktypen"

    def get_paginated_items(
        self,
        params: dict | None = None,
    ) -> ZaakTypenPaginatedResponse:
        params = params or {}
        data = self.make_request(self.endpoint, params)
        results = [self._map_zaaktype(record) for record in data.get("results", [])]
        return ZaakTypenPaginatedResponse(count=data["count"], results=results)

    def get_item_by_uuid(self, uuid: str) -> ZaakType | NoReturn:
        data = self.make_request(f"{self.endpoint}/{uuid}")
        return self._map_zaaktype(data)

    @staticmethod
    def _map_zaaktype(record: dict) -> ZaakType:
        return ZaakType(
            uuid=extract_uuid(record["url"]),
            url=record["url"],
            catalogus=record["catalogus"],
            concept=record["concept"],
            identificatie=record["identificatie"],
            omschrijving=record["omschrijving"],
            versiedatum=record["versiedatum"],
            beginGeldigheid=record["beginGeldigheid"],
            eindeGeldigheid=record["eindeGeldigheid"],
        )

    def get_paginated_cached_items(
        self,
        service_slug: str,
        params: dict | None = None,
        cache_timeout: int = 300,
    ) -> ZaakTypenPaginatedResponse:
        params = params or {}
        if params:
            return self.get_paginated_items(params)

        return cache.get_or_set(
            key=f"zaaktypen:{service_slug}:",
            default=partial(self.get_paginated_items, params),
            timeout=cache_timeout,
        )


def get_zaaktypen_client(service: Service) -> ZaakTypeClient:
    return build_client(service, client_factory=ZaakTypeClient)
