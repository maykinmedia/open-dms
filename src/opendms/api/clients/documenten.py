from zgw_consumers.client import build_client
from zgw_consumers.models import Service
from zgw_consumers.nlx import NLXClient
from zgw_consumers.service import pagination_helper

from opendms.api.utils.validators import extract_uuid

from ..typing import DocumentsPaginatedResponse, DocumentType
from ..utils.mixins import HttpRequestMixin

CRS_HEADERS = {"Content-Crs": "EPSG:4326", "Accept-Crs": "EPSG:4326"}


class DocumentClient(HttpRequestMixin, NLXClient):
    """
    Client for retrieving all Documenten from an OpenZaak service.
    """

    endpoint = "enkelvoudiginformatieobjecten"

    def get_items(self, params: dict | None = None) -> list[DocumentType]:
        """
        Fetch all documenten using pagination
        """
        params = params or {}
        params = {**params, "objectinformatieobjecten__objectType": "zaak"}

        data = self.make_request(self.endpoint, {})
        return [self._map_document(record) for record in pagination_helper(self, data)]

    def get_item_by_uuid(self, uuid: str) -> DocumentType:
        data = self.make_request(f"{self.endpoint}/{uuid}")
        return self._map_document(data)

    def get_paginated_items_by_zaak(
        self, zaak_url: str, params: dict | None = None
    ) -> DocumentsPaginatedResponse:
        params = params or {}
        data = self.make_request(
            self.endpoint,
            params={**params, "objectinformatieobjecten__object": zaak_url},
            headers=CRS_HEADERS,
        )
        results = [self._map_document({**record}) for record in data.get("results", [])]
        return DocumentsPaginatedResponse(count=data.get("count", 0), results=results)

    @staticmethod
    def _map_document(record: dict) -> DocumentType:
        return DocumentType(
            uuid=extract_uuid(record["url"]),
            url=record["url"],
            identificatie=record["identificatie"],
            bronorganisatie=record["bronorganisatie"],
            creatiedatum=record["creatiedatum"],
            titel=record["titel"],
            auteur=record["auteur"],
            taal=record["taal"],
            begin_registratie=record["beginRegistratie"],
            informatieobjecttype=record["informatieobjecttype"],
            vertrouwelijkheidaanduiding=record["vertrouwelijkheidaanduiding"],
            status=record["status"],
            formaat=record["formaat"],
            bestandsnaam=record["bestandsnaam"],
            inhoud=record["inhoud"],
            link=record["link"],
            beschrijving=record["beschrijving"],
            verschijningsvorm=record["verschijningsvorm"],
            bestandsomvang=record["bestandsomvang"],
        )


def get_documenten_client(service: Service) -> DocumentClient:
    return build_client(service, client_factory=DocumentClient)
