from django.urls import path, include
from drf_spectacular.views import SpectacularRedocView, SpectacularJSONAPIView, SpectacularAPIView

urlpatterns = [
  # API documentation
  path("docs/", SpectacularRedocView.as_view(url_name="api-schema-json"), name="api-docs"),
  path("v1/",
    include(
      [
        path("", SpectacularJSONAPIView.as_view(schema=None), name="api-schema-json"),
        path("schema", SpectacularAPIView.as_view(schema=None), name="schema"),
        path("", include("opendms.accounts.api.urls"), name="accounts"),
      ]
    ),
  ),
]
