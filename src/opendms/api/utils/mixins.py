from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

import structlog
from requests.exceptions import RequestException, Timeout
from rest_framework import exceptions, status
from rest_framework.request import Request
from rest_framework.response import Response
from zgw_consumers.models import Service

from ..models import ZGWApiGroupConfig
from .exceptions import ExternalServiceUnavailable, ZGWGroupConfigurationMissing

logger = structlog.stdlib.get_logger(__name__)


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


class HttpRequestMixin:
    """
    Mixin to centralize HTTP requests and common error handling.
    """

    def make_request(
        self,
        url: str,
        params: dict | None = None,
        headers: dict | None = None,
    ) -> dict:
        """
        Performs a GET request to `url` with optional query parameters.
        Handles timeouts, connection errors, and 404 responses.
        """
        params = params or {}
        headers = headers or {}
        try:
            response = self.get(url, params=params, headers=headers)

            if response.status_code == status.HTTP_404_NOT_FOUND:
                raise exceptions.NotFound(f"Resource at {url} not found")

            response.raise_for_status()
            return response.json()

        except Timeout as exc:
            logger.exception("timeout_request")
            raise ExternalServiceUnavailable("External service timeout") from exc

        except RequestException as exc:
            logger.exception("error_request")
            raise ExternalServiceUnavailable("External service error") from exc


class ReadOnlyViewSetMixin:
    _zgw_group: Service | None = None
    _service: Service | None = None

    @property
    def zgw_group(self) -> Service:
        """
        Return the ZGW service group associated with the relativ ztc_service

        The service is resolved using the `service_slug` URL parameter.
        The result is cached on first access to avoid repeated lookups
        during the request lifecycle.
        """
        if self._zgw_group is None:
            self._zgw_group = get_group_from_ztc_service(self.service)

        return self._zgw_group

    @property
    def service(self) -> Service:
        """
        Returns the Service configuration associated with the request.

        The service is resolved using the ``service_slug`` URL parameter
        and cached on first access for reuse during the request lifecycle.
        """
        if self._service is None:
            service_slug = self.kwargs.get("service_slug")
            if not service_slug:
                raise exceptions.NotFound(_("Service slug missing"))

            self._service = get_object_or_404(Service, slug=service_slug)

        return self._service

    def get_serializer_context(self):
        return {"request": self.request, "format": self.format_kwarg, "view": self}

    def get_serializer(self, *args, **kwargs):
        kwargs["context"] = self.get_serializer_context()
        return self.serializer_class(*args, **kwargs)

    def list(self, request: Request, *args, **kwargs) -> Response:
        items = self.get_queryset(request.query_params)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(items, request)
        if page is not None:
            serializer = self.serializer_class(
                page, many=True, context=self.get_serializer_context()
            )
            return paginator.get_paginated_response(serializer.data)

        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)

    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
