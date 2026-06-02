from uuid import UUID

from zgw_consumers.client import build_client
from zgw_consumers.models import Service
from zgw_consumers.nlx import NLXClient

from ..typing import InformatieObjectType, InformatieObjectTypenPaginatedResponse
from ..utils.mixins import HttpRequestMixin
from ..utils.validators import extract_uuid


class InformatieObjectTypeClient(HttpRequestMixin, NLXClient):
    endpoint = "informatieobjecttypen"

    def get_paginated_items(
        self,
        params: dict | None = None,
    ) -> InformatieObjectTypenPaginatedResponse:
        params = params or {}

        data = self.make_request(
            self.endpoint,
            params=params,
        )

        results = [
            self._map_informatieobjecttype(record) for record in data.get("results", [])
        ]

        return InformatieObjectTypenPaginatedResponse(
            count=data.get("count", len(results)),
            results=results,
        )

    def get_item_by_uuid(
        self,
        uuid: str,
    ) -> InformatieObjectType:
        data = self.make_request(f"{self.endpoint}/{uuid}")
        return self._map_informatieobjecttype(data)

    @staticmethod
    def _map_informatieobjecttype(
        record: dict,
    ) -> InformatieObjectType:
        return InformatieObjectType(
            uuid=UUID(extract_uuid(record["url"])),
            url=record["url"],
            catalogus=record["catalogus"],
            omschrijving=record["omschrijving"],
            vertrouwelijkheidaanduiding=record["vertrouwelijkheidaanduiding"],
            beginGeldigheid=record["beginGeldigheid"],
            eindeGeldigheid=record["eindeGeldigheid"],
            concept=record["concept"],
            informatieobjectcategorie=record["informatieobjectcategorie"],
            zaaktypen=record.get("zaaktypen", []),
        )


def get_informatieobjecttypen_client(
    service: Service,
) -> InformatieObjectTypeClient:
    return build_client(
        service,
        client_factory=InformatieObjectTypeClient,
    )
