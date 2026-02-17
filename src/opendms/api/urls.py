from django.urls import include, path

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularJSONAPIView,
    SpectacularRedocView,
)

app_name = "api"

urlpatterns = [
    # API documentation
    path(
        "docs/",
        SpectacularRedocView.as_view(url_name="api:v1:api-schema-json"),
        name="api-docs",
    ),
    path(
        "v1/",
        include(
            (
                [
                    path(
                        "",
                        SpectacularJSONAPIView.as_view(schema=None),
                        name="api-schema-json",
                    ),
                    path(
                        "schema", SpectacularAPIView.as_view(schema=None), name="schema"
                    ),
                    path(
                        "", include("opendms.accounts.api.urls", namespace="accounts")
                    ),
                ],
                "v1",
            ),
            namespace="v1",
        ),
    ),
]
