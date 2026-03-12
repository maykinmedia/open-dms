from zgw_consumers.client import build_client
from zgw_consumers.models import Service
from zgw_consumers.nlx import NLXClient
from zgw_consumers.service import pagination_helper

from ..typing import ZaakAPI
from ..utils.mixins import HttpRequestMixin

CRS_HEADERS = {"Content-Crs": "EPSG:4326", "Accept-Crs": "EPSG:4326"}


class ZaakClient(HttpRequestMixin, NLXClient):
    """
    Client for retrieving Zaken from a ZRC service.
    """

    endpoint = "zaken"

    def get_items_by_zaaktype(self, zaaktype_url: str) -> list[ZaakAPI]:
        params = {"zaaktype": zaaktype_url}
        data = self.make_request(self.endpoint, params=params, headers=CRS_HEADERS)
        return [
            ZaakAPI(
                uuid=record["uuid"],
                url=record["url"],
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
        data = self.make_request(f"{self.endpoint}/{uuid}", headers=CRS_HEADERS)
        return ZaakAPI(
            uuid=data["uuid"],
            url=data["url"],
            identificatie=data["identificatie"],
            zaaktype=data["zaaktype"],
            bronorganisatie=data["bronorganisatie"],
            verantwoordelijkeOrganisatie=data["verantwoordelijkeOrganisatie"],
            registratiedatum=data["registratiedatum"],
            startdatum=data["startdatum"],
            omschrijving=data["omschrijving"],
            toelichting=data["toelichting"],
        )

    # TODO investigate for get_cached_items


def get_zaken_client(service: Service) -> ZaakClient:
    return build_client(service, client_factory=ZaakClient)
