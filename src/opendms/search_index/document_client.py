from zgw_consumers.client import build_client
from zgw_consumers.models import Service
from zgw_consumers.nlx import NLXClient
from zgw_consumers.service import pagination_helper

from opendms.api.utils.exceptions import NoServiceConfigured
from opendms.api.utils.validators import extract_uuid

from .typing import DocumentType


class DocumentClient(NLXClient):
    """
    Client for retrieving all Documenten from an OpenZaak service.
    """

    endpoint = "enkelvoudiginformatieobjecten"

    def get_items(self, filters: dict | None = None) -> list[DocumentType]:
        """
        Fetch all documenten using pagination.
        """
        params = filters or {}
        response = self.get(self.endpoint, params=params)
        response.raise_for_status()
        data = response.json()

        return [
            DocumentType(
                uuid=extract_uuid(record["url"]),
                identificatie=record["identificatie"],
                bronorganisatie=record["bronorganisatie"],
                creatiedatum=record["creatiedatum"],
                titel=record["titel"],
                auteur=record.get("auteur"),
                taal=record.get("taal"),
                begin_registratie=record.get("beginRegistratie"),
                informatieobjecttype=record["informatieobjecttype"],
                vertrouwelijkheidaanduiding=record.get("vertrouwelijkheidaanduiding"),
                status=record.get("status"),
                formaat=record.get("formaat"),
                bestandsnaam=record.get("bestandsnaam"),
                link=record.get("link"),
                inhoud=record.get("inhoud"),
                beschrijving=record.get("beschrijving"),
                verschijningsvorm=record.get("verschijningsvorm"),
            )
            for record in pagination_helper(self, data)
        ]


def get_documenten_client(service: Service) -> DocumentClient:
    if service is None:
        raise NoServiceConfigured("No Documenten API service configured!")
    return build_client(service, client_factory=DocumentClient)
