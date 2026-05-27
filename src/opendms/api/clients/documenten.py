import base64

from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _

import structlog
from requests.exceptions import RequestException, Timeout
from rest_framework import exceptions, status
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
from ..utils.file import guess_extension_by_response
from ..utils.mixins import HttpRequestMixin

CRS_HEADERS = {"Content-Crs": "EPSG:4326", "Accept-Crs": "EPSG:4326"}


logger = structlog.stdlib.get_logger(__name__)


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

    def download_document(self, document: DocumentType) -> HttpResponse:
        document_url = document["inhoud"]

        if not document_url:
            raise exceptions.NotFound(
                _("Resource at {url} not found").format(url=document_url)
            )

        response = self.get(document_url)

        if response.status_code == 204:
            return HttpResponse(status=204)

        name = document.get("name", document["identificatie"])
        extension = guess_extension_by_response(response)
        fullname = f"{name}{extension}"

        # Hop-by-hop headers must be stripped before forwarding — wsgiref rejects them.
        hop_by_hop = {
            "connection",
            "keep-alive",
            "proxy-authenticate",
            "proxy-authorization",
            "te",
            "trailers",
            "transfer-encoding",
            "upgrade",
        }
        safe_headers = {
            k: v
            for k, v in response.headers.items()
            if k.lower() not in hop_by_hop
        }

        return HttpResponse(
            response.content,
            headers={
                **safe_headers,
                "Content-Disposition": f'attachment; filename="{fullname}"',
                "File-Name": fullname,
                "File-Extension": extension,
            },
        )

    def upload_document(
        self,
        document_uuid: str,
        content: bytes,
        size: int,
        mime_type: str = "application/octet-stream",
    ) -> int:
        """
        Upload a document to the API.
        Locks the resource, uploads the content, then unlocks it.
        The lock is always released even if the upload fails.

        """
        try:
            lock_response = self.post(f"{self.endpoint}/{document_uuid}/lock")
            lock_response.raise_for_status()
            lock = lock_response.json().get("lock", "")

            try:
                response = self.patch(
                    f"{self.endpoint}/{document_uuid}",
                    json={
                        "inhoud": base64.b64encode(content).decode("utf-8"),
                        "lock": lock,
                        "bestandsomvang": size,
                    },
                )
                response.raise_for_status()
                return status.HTTP_200_OK, "Document Uploaded"
            finally:
                unlock_response = self.post(f"{self.endpoint}/{document_uuid}/unlock")
                unlock_response.raise_for_status()

        except Timeout:
            logger.exception("timeout__request", document_uuid=document_uuid)
            return status.HTTP_408_REQUEST_TIMEOUT, "Request Timeout"

        except RequestException:
            logger.exception("error_request", document_uuid=document_uuid)
            return status.HTTP_503_SERVICE_UNAVAILABLE, "Service Unavailable"

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

    def get_unlinked_documents_by_iot(
        self,
        iot_url: str,
        oio_client: "ObjectInformatieObjectClient",
        params: dict | None = None,
    ) -> DocumentsPaginatedResponse:
        """
        Return documents of a given informatieobjecttype that have no zaak OIO link.
        Fetches all pages of EIOs for the IOT, filters against the set of zaak-linked
        document URLs from the OIO endpoint, and re-paginates in this layer.
        """
        params = params or {}
        page = int(params.get("page", 1))
        page_size = int(params.get("pageSize", 20))

        linked_urls = oio_client.get_all_zaak_linked_urls()

        first_page = self.make_request(
            self.endpoint,
            params={"informatieobjecttype": iot_url},
        )
        all_records = list(pagination_helper(self, first_page))
        unlinked = [r for r in all_records if r["url"] not in linked_urls]
        mapped = [self._map_document(r) for r in unlinked]

        start = (page - 1) * page_size
        end = start + page_size
        return DocumentsPaginatedResponse(count=len(mapped), results=mapped[start:end])

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

    def get_all_zaak_linked_urls(self) -> set[str]:
        """
        Return the set of informatieobject URLs that are linked to a zaak via an OIO.
        OIOs are returned as a flat list (not paginated) by the DRC API.
        """
        data = self.make_request(self.endpoint, headers=CRS_HEADERS)
        return {
            item["informatieobject"]
            for item in data
            if item.get("objectType") == "zaak"
        }


def get_oio_client(service: Service) -> ObjectInformatieObjectClient:
    return build_client(service, client_factory=ObjectInformatieObjectClient)


def get_documenten_client(service: Service) -> DocumentClient:
    return build_client(service, client_factory=DocumentClient)
