from collections.abc import Mapping
from typing import NoReturn
from uuid import UUID

from zgw_consumers.client import build_client
from zgw_consumers.models import Service
from zgw_consumers.nlx import NLXClient

from ..typing import PaginatedResponse, StatusType
from ..utils.mixins import HttpRequestMixin
from ..utils.validators import extract_uuid


class StatusTypeClient(HttpRequestMixin, NLXClient):
    """
    Client for retrieving Statustypen from a ZTC service.
    """

    endpoint = "statustypen"

    def get_paginated_items(
        self,
        params: Mapping[str, object] = {},
    ) -> PaginatedResponse[StatusType]:
        data = self.make_request(self.endpoint, params)

        match data:
            case {"results": list(results), "count": int(count)}:
                return PaginatedResponse(
                    count=count,
                    results=[
                        self._map_statustype(record)
                        for record in results
                        if isinstance(record, dict)  # XXX: silent ignore!
                    ],
                )
            case _:
                raise ValueError("Malformed service response")

    def get_item_by_uuid(self, uuid: str) -> StatusType | NoReturn:
        data = self.make_request(f"{self.endpoint}/{uuid}")
        assert isinstance(data, dict)  # TODO: parse, don't validate :(
        return self._map_statustype(data)

    @staticmethod
    def _map_statustype(record: dict) -> StatusType:
        # TODO: parse response into StatusType or validate record
        # This is just YOLO'ing Unknowns
        return StatusType(
            uuid=UUID(extract_uuid(record["url"])),
            url=record["url"],
            omschrijving=record["omschrijving"],
            omschrijvingGeneriek=record.get("omschrijvingGeneriek", ""),
            statustekst=record.get("statustekst", ""),
            zaaktype=record["zaaktype"],
            catalogus=record["catalogus"],
            zaaktypeIdentificatie=record["zaaktypeIdentificatie"],
            volgnummer=record["volgnummer"],
            isEindstatus=record["isEindstatus"],
            informeren=record.get("informeren", False),
            doorlooptijd=record.get("doorlooptijd"),
            toelichting=record.get("toelichting"),
            checklistitemStatustype=record.get("checklistitemStatustype", []),
            eigenschappen=record.get("eigenschappen", []),
        )


def get_statustypen_client(service: Service) -> StatusTypeClient:
    return build_client(service, client_factory=StatusTypeClient)
