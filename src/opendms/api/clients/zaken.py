from functools import partial

from django.core.cache import cache

from zgw_consumers.client import build_client
from zgw_consumers.models import Service
from zgw_consumers.nlx import NLXClient
from zgw_consumers.service import pagination_helper
from uuid import UUID
from rest_framework import status
from ..typing import ZaakAPI
from ..utils.exceptions import NoServiceConfigured
from ..utils.validators import extract_uuid

CRS_HEADERS = {"Content-Crs": "EPSG:4326", "Accept-Crs": "EPSG:4326"}


class ZaakClient(NLXClient):
    """
    Client for retrieving Zaken from a ZRC service.
    """

    endpoint = "zaken"

    def get_items(self, params: dict) -> list[ZaakAPI]:
        response = self.get(self.endpoint, params=params, headers=CRS_HEADERS)
        response.raise_for_status()
        data = response.json()
        return [
            ZaakAPI(
                uuid=extract_uuid(record["url"]),
                identificatie=record["identificatie"],
                zaaktype=record["zaaktype"],
                bronorganisatie=record["bronorganisatie"],
                verantwoordelijkeOrganisatie=record["verantwoordelijkeOrganisatie"],
                registratiedatum=record["registratiedatum"],
                startdatum=record["startdatum"],
                omschrijving=record["omschrijving"],
                toelichting=record["toelichting"],
            )
            for record in pagination_helper(self, data)
        ]

    def get_items_by_zaaktype(self, zaaktype_url: str) -> list[ZaakAPI]:
        params = {"zaaktype": zaaktype_url}
        response = self.get(self.endpoint, params=params, headers=CRS_HEADERS)
        response.raise_for_status()
        data = response.json()
        return [
            ZaakAPI(
                uuid=extract_uuid(record["url"]),
                identificatie=record["identificatie"],
                zaaktype=record["zaaktype"],
                bronorganisatie=record["bronorganisatie"],
                verantwoordelijkeOrganisatie=record["verantwoordelijkeOrganisatie"],
                registratiedatum=record["registratiedatum"],
                startdatum=record["startdatum"],
                omschrijving=record["omschrijving"],
                toelichting=record["toelichting"],
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
        raise NoServiceConfigured("No Zaken API service configured!")

    return build_client(service, client_factory=ZaakClient)
