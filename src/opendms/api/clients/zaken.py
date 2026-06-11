from collections.abc import Iterable, Mapping
from typing import NotRequired

from msgspec.json import decode
from zgw_consumers.client import build_client
from zgw_consumers.models import Service
from zgw_consumers.nlx import NLXClient
from zgw_consumers.service import pagination_helper
from zgw_consumers.utils import PaginatedResponseData as _ZGWConsumerPage

from ..typing import ESZaak, PaginatedResponse, Zaak
from ..utils.mixins import HttpRequestMixin

CRS_HEADERS = {"Content-Crs": "EPSG:4326", "Accept-Crs": "EPSG:4326"}


class PaginatedResponseData[T](_ZGWConsumerPage):
    # the ZGW Consumers version is wrong
    # maykinmedia/zgw-consumers#139
    # TODO: remove when that fix is  released
    count: int
    next: NotRequired[str | None]  # type: ignore
    previous: NotRequired[str | None]  # type: ignore
    results: list[T]


class ZaakClient(HttpRequestMixin, NLXClient):
    """
    Client for retrieving Zaken from a ZRC service.
    """

    endpoint = "zaken"

    def get_zaken_for_elasticsearch(
        self, params: Mapping[str, object] = {}
    ) -> Iterable[ESZaak]:
        """
        Fetch all zaken using pagination, this is used for indexing zaken in Elasticsearch.
        """
        data = self.make_request(
            self.endpoint,
            params=params,
            headers=CRS_HEADERS,
            parse_into=PaginatedResponseData[ESZaak],
        )
        return pagination_helper(self, data)  # pyright: ignore[reportArgumentType]

    def get_items(self, params: Mapping[str, object] = {}) -> Iterable[Zaak]:
        """
        Fetch all zaken using pagination, this is used for retrieving zaken for the API.
        """
        data = self.make_request(
            self.endpoint,
            params=params,
            headers=CRS_HEADERS,
            parse_into=PaginatedResponseData[Zaak],
        )
        return pagination_helper(self, data)  # pyright: ignore[reportArgumentType]

    def get_paginated_items(
        self, params: Mapping[str, object] = {}
    ) -> PaginatedResponse[Zaak]:
        return self.make_request(
            self.endpoint,
            params=params,
            headers=CRS_HEADERS,
            parse_into=PaginatedResponse[Zaak],
        )

    def get_paginated_items_by_zaaktype(
        self,
        zaaktype_url: str,
        params: Mapping[str, object] = {},
    ) -> PaginatedResponse[Zaak]:
        return self.make_request(
            self.endpoint,
            params={**params, "zaaktype": zaaktype_url},
            headers=CRS_HEADERS,
            parse_into=PaginatedResponse[Zaak],
        )

    def get_item_by_uuid(self, uuid: str) -> Zaak | None:
        return self.make_request(
            f"{self.endpoint}/{uuid}", headers=CRS_HEADERS, parse_into=Zaak
        )

    # TODO investigate for get_cached_items

    def create_zaak(self, data: dict) -> Zaak:
        response = self.post(
            self.endpoint,
            json=data,
            headers=CRS_HEADERS,
        )
        response.raise_for_status()
        return decode(response.content, type=Zaak)


def get_zaken_client(service: Service) -> ZaakClient:
    return build_client(service, client_factory=ZaakClient)
