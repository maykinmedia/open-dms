from django.http import StreamingHttpResponse
from django.utils.translation import gettext_lazy as _

from rest_framework import exceptions
from zgw_consumers.client import build_client
from zgw_consumers.models import Service
from zgw_consumers.nlx import NLXClient
from zgw_consumers.service import pagination_helper

from opendms.api.utils.validators import extract_uuid

from ..typing import (
    DocumentsPaginatedResponse,
    DocumentType,
    ObjectInformatieObjectType,
)
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
        data = self.make_request(
            self.endpoint,
            params={**params, "objectinformatieobjecten__objectType": "zaak"},
        )
        return [self._map_document(record) for record in pagination_helper(self, data)]

    def get_item_by_uuid(self, uuid: str) -> DocumentType:
        data = self.make_request(f"{self.endpoint}/{uuid}")
        return self._map_document(data)

    def download_document(self, document_url: str) -> DocumentType:
        if not document_url:
            raise exceptions.NotFound(
                _("Resource at {url} not found").format(url=document_url)
            )

        response = self.get(document_url, stream=True)

        if response.status_code == 204:
            return StreamingHttpResponse(status=204)

        file_response = StreamingHttpResponse(
            response.iter_content(chunk_size=8192), headers=response.headers
        )
        return file_response

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

    def retrieve(self, uuid: str) -> dict:
        url = f"{self.endpoint}/{uuid}"
        response = self.make_request(url)
        return response


class ObjectInformatieObjectClient(HttpRequestMixin, NLXClient):
    """
    Client for retrieving ObjectInformatieObjecten (OIO).
    Links documents to related Zaken.
    """

    endpoint = "objectinformatieobjecten"

    def get_by_informatieobject(
        self, document_url: str
    ) -> list[ObjectInformatieObjectType]:
        """
        Fetch all OIOs for a given document URL.
        """
        data = self.make_request(
            self.endpoint,
            params={"informatieobject": document_url},
            headers=CRS_HEADERS,
        )
        return data


def get_oio_client(service: Service) -> ObjectInformatieObjectClient:
    return build_client(service, client_factory=ObjectInformatieObjectClient)


def get_documenten_client(service: Service) -> DocumentClient:
    return build_client(service, client_factory=DocumentClient)
