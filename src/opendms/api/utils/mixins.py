from __future__ import annotations

from abc import abstractmethod
from collections.abc import Mapping
from json import JSONDecodeError
from typing import TYPE_CHECKING, NoReturn

from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

import structlog
from ape_pie import APIClient
from requests.exceptions import RequestException, Timeout
from rest_framework import exceptions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet
from zgw_consumers.models import Service

from ..models import ZGWApiGroupConfig
from ..typing import JSONValue, PaginatedResponse
from .exceptions import ExternalServiceUnavailable, ZGWGroupConfigurationMissing

logger = structlog.stdlib.get_logger(__name__)

if TYPE_CHECKING:
    _HttpRequestMixinBase = APIClient

    class _ViewSetMixinBase(ReadOnlyModelViewSet):
        # Poor man's Protocol
        @abstractmethod
        def get_paginated_queryset(
            self, params: Mapping[str, object]
        ) -> PaginatedResponse: ...
else:
    _HttpRequestMixinBase = _ViewSetMixinBase = object


def get_group_from_ztc_service(service: Service) -> ZGWApiGroupConfig:
    try:
        return ZGWApiGroupConfig.objects.get(ztc_service=service)
    except ZGWApiGroupConfig.DoesNotExist as exc:
        logger.exception("zgw_apigroup_config_does_not_exist")
        raise ZGWGroupConfigurationMissing(
            _(
                "No configuration group was found containing this ZTC service: '{service_slug}'"
            ).format(service_slug=service.slug)
        ) from exc


class HttpRequestMixin(_HttpRequestMixinBase):
    """
    Mixin to centralize HTTP requests and common error handling.
    """

    def make_request(
        self,
        url: str,
        params: Mapping = {},
        headers: Mapping = {},
    ) -> JSONValue | NoReturn:
        """
        Performs a GET request to `url` with optional query parameters.
        Handles timeouts, connection errors, and 404 responses.
        """

        try:
            response = self.get(url, params=params, headers=headers)

            match response.status_code:
                case status.HTTP_404_NOT_FOUND:
                    raise exceptions.NotFound(
                        _("Resource at {url} not found").format(url=url)
                    )

                case status.HTTP_400_BAD_REQUEST:
                    # raise a generic message
                    logger.exception("bad_request")
                    raise exceptions.ValidationError(
                        _("Invalid or unsupported query parameters."),
                        code="bad-request",
                    )

            response.raise_for_status()

            return response.json()

        except Timeout as exc:
            logger.exception("timeout_request")
            raise ExternalServiceUnavailable("External service timeout") from exc

        except RequestException as exc:
            logger.exception("error_request")
            raise ExternalServiceUnavailable("External service error") from exc
        except JSONDecodeError:
            logger.exception("service_response_json_error")
            raise


class ReadOnlyViewSetMixin(_ViewSetMixinBase):
    _service: Service | None = None

    @property
    def zgw_group(self) -> ZGWApiGroupConfig:
        """
        Return the ZGW service group associated with the relative ztc_service

        The service is resolved using the `service_slug` URL parameter.
        The result is cached on first access to avoid repeated lookups
        during the request lifecycle.
        """

        return get_group_from_ztc_service(self.service)

    @property
    def service(self) -> Service:
        """
        Returns the Service configuration associated with the request.

        The service is resolved using the ``service_slug`` URL parameter
        and cached on first access for reuse during the request lifecycle.
        """
        if self._service is None:
            self._service = get_object_or_404(
                Service,
                slug=self.kwargs.get("service_slug", ""),
            )
        return self._service

    def get_serializer_context(self) -> dict:
        return {"request": self.request, "format": self.format_kwarg, "view": self}

    def get_serializer(self, *args, **kwargs):
        kwargs["context"] = self.get_serializer_context()
        assert self.serializer_class
        return self.serializer_class(*args, **kwargs)

    def list(self, request: Request, *args, **kwargs) -> Response:
        data = self.get_paginated_queryset(request.query_params)
        serializer = self.get_serializer(data["results"], many=True)
        return Response(PaginatedResponse(count=data["count"], results=serializer.data))

    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
