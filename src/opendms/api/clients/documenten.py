from zgw_consumers.client import build_client
from zgw_consumers.models import Service
from zgw_consumers.nlx import NLXClient
from zgw_consumers.service import pagination_helper

from opendms.api.utils.validators import extract_uuid

from ...search_index.typing import DocumentType
from ..utils.mixins import HttpRequestMixin


class DocumentClient(HttpRequestMixin, NLXClient):
    """
    Client for retrieving all Documenten from an OpenZaak service.
    """

    endpoint = "enkelvoudiginformatieobjecten"

    def get_items(self, params: dict | None = None) -> list[DocumentType]:
        """
        Fetch all documenten using pagination.
        """
        params = params or {}
        params = {**params, "objectinformatieobjecten__objectType": "zaak"}
        data = self.make_request(self.endpoint, params)

        return [
            DocumentType(
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
            for record in pagination_helper(self, data)
        ]


def get_documenten_client(service: Service) -> DocumentClient:
    return build_client(service, client_factory=DocumentClient)
