from django.urls import include, path, re_path

from drf_spectacular.views import SpectacularRedocView
from vng_api_common import routers

from opendms.api.utils.views import SpectacularJSONAPIView, SpectacularYAMLAPIView

from .viewsets import (
    DocumentRegistrerenViewSet,
    DocumentViewSet,
    InformatieObjectTypeViewSet,
    SearchView,
    ServiceViewSet,
    ServiceZaakInformatieObjectViewSet,
    ServiceZaakViewSet,
    StatusTypeListViewSet,
    StatusTypeViewSet,
    ZaakTypeViewSet,
    ZaakViewSet,
)

app_name = "api"

router = routers.DefaultRouter()
router.register("services", ServiceViewSet)

service_router = routers.NestedSimpleRouter(
    router,
    r"services",
    lookup="service",
)
service_router.register(
    r"zaaktypen",
    ZaakTypeViewSet,
    basename="zaaktypen",
    nested=[
        routers.Nested(
            r"statustypen",
            StatusTypeListViewSet,
            basename="zaaktype-statustypen",
        ),
    ],
)
service_router.register(
    r"zaken",
    ServiceZaakViewSet,
    basename="service-zaken",
)
service_router.register(
    r"zaakinformatieobjecten",
    ServiceZaakInformatieObjectViewSet,
    basename="service-zaakinformatieobjecten",
)
service_router.register(
    r"statustypen",
    StatusTypeViewSet,
    basename="statustypen",
)


zaken_router = routers.NestedSimpleRouter(
    service_router,
    r"zaaktypen",
    lookup="zaaktypen",
)
zaken_router.register(
    r"zaken",
    ZaakViewSet,
    basename="zaken",
)
documents_router = routers.NestedSimpleRouter(
    zaken_router,
    r"zaken",
    lookup="zaken",
)
documents_router.register(
    r"documents",
    DocumentViewSet,
    basename="documents",
)
service_router.register(
    r"informatieobjecttypen",
    InformatieObjectTypeViewSet,
    basename="informatieobjecttypen",
)
service_router.register(
    r"document_registreren",
    DocumentRegistrerenViewSet,
    basename="service-document-registreren",
)
urlpatterns = [
    re_path(
        r"^v(?P<version>\d+)/",
        include(
            [
                re_path(r"^", include(router.urls)),
                re_path(r"^", include(service_router.urls)),
                re_path(r"^", include(zaken_router.urls)),
                re_path(r"^", include(documents_router.urls)),
                path(
                    "accounts/",
                    include("opendms.accounts.api.urls", namespace="accounts"),
                ),
                path(
                    "openapi.json",
                    SpectacularJSONAPIView.as_view(
                        urlconf="opendms.api.urls",
                    ),
                    name="schema-json-api",
                ),
                path(
                    "openapi.yaml",
                    SpectacularYAMLAPIView.as_view(
                        urlconf="opendms.api.urls",
                    ),
                    name="schema-yaml-api",
                ),
                path(
                    "schema/",
                    SpectacularRedocView.as_view(url_name="api:schema-yaml-api"),
                    name="schema-redoc-api",
                ),
                path("search", SearchView.as_view(), name="search"),
                *router.urls,
            ]
        ),
    ),
]
