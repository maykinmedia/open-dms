from zgw_consumers.client import build_client
from zgw_consumers.models import Service
from zgw_consumers.nlx import NLXClient
from zgw_consumers.service import pagination_helper

from ..typing import ESZaak, Zaak, ZakenPaginatedResponse
from ..utils.mixins import HttpRequestMixin

CRS_HEADERS = {"Content-Crs": "EPSG:4326", "Accept-Crs": "EPSG:4326"}


class ZaakClient(HttpRequestMixin, NLXClient):
    """
    Client for retrieving Zaken from a ZRC service.
    """

    endpoint = "zaken"

    def get_zaken_for_elasticsearch(self, params: dict | None = None) -> list[ESZaak]:
        """
        Fetch all zaken using pagination, this is used for indexing zaken in Elasticsearch.
        """
        params = params or {}
        data = self.make_request(
            self.endpoint,
            params={**params},
            headers=CRS_HEADERS,
        )
        return [self._map_zaak(record) for record in pagination_helper(self, data)]

    def get_paginated_items_by_zaaktype(
        self,
        zaaktype_url: str,
        params: dict | None = None,
    ) -> ZakenPaginatedResponse:
        params = params or {}
        data = self.make_request(
            self.endpoint,
            params={**params, "zaaktype": zaaktype_url},
            headers=CRS_HEADERS,
        )
        results = [self._map_zaak(record) for record in data.get("results", [])]
        return ZakenPaginatedResponse(count=data.get("count", 0), results=results)

    def get_item_by_uuid(self, uuid: str) -> Zaak | None:
        data = self.make_request(f"{self.endpoint}/{uuid}", headers=CRS_HEADERS)
        return self._map_zaak(data)

    @staticmethod
    def _map_zaak(record: dict) -> Zaak:
        return Zaak(
            uuid=record["uuid"],
            url=record["url"],
            identificatie=record["identificatie"],
            zaaktype=record["zaaktype"],
            bronorganisatie=record["bronorganisatie"],
            verantwoordelijkeOrganisatie=record["verantwoordelijkeOrganisatie"],
            registratiedatum=record["registratiedatum"],
            startdatum=record["startdatum"],
            omschrijving=record.get("omschrijving"),
            toelichting=record.get("toelichting"),
        )

    # TODO investigate for get_cached_items


def get_zaken_client(service: Service) -> ZaakClient:
    return build_client(service, client_factory=ZaakClient)
