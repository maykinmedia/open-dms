from vng_api_common.conf.api import *  # noqa - imports white-listed


API_VERSION = "1.0.0"

REST_FRAMEWORK = BASE_REST_FRAMEWORK.copy()
REST_FRAMEWORK["PAGE_SIZE"] = 100

REST_FRAMEWORK["DEFAULT_PAGINATION_CLASS"] = (
    "opendms.api.utils.pagination.CountedPagination"
)
REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = (
    "rest_framework.authentication.SessionAuthentication",
)
REST_FRAMEWORK["DEFAULT_PERMISSION_CLASSES"] = (
    # "rest_framework.permissions.IsAuthenticated",
)

REST_FRAMEWORK["DEFAULT_SCHEMA_CLASS"] = "opendms.api.utils.schema.AutoSchema"
#
# SPECTACULAR - OpenAPI schema generation
#
API_DESCRIPTION = """
Open DMS
"""

SPECTACULAR_SETTINGS = {
    "REDOC_DIST": "SIDECAR",
    "SERVE_INCLUDE_SCHEMA": False,
    "TITLE": "Open DMS API",
    "DESCRIPTION": API_DESCRIPTION,
    "VERSION": API_VERSION,
    "CAMELIZE_NAMES": True,
    "SCHEMA_PATH_PREFIX": r"/v[0-9]+",
    "SCHEMA_PATH_PREFIX_TRIM": True,
    "ENUM_GENERATE_CHOICE_DESCRIPTION": False,
    "POSTPROCESSING_HOOKS": [
        "drf_spectacular.hooks.postprocess_schema_enums",
        "drf_spectacular.contrib.djangorestframework_camel_case.camelize_serializer_fields",
        "maykin_common.drf_spectacular.hooks.remove_invalid_url_defaults",
    ],
    "CONTACT": {
        "email": "standaarden.ondersteuning@vng.nl",
        "name": "VNG",
        "url": "https://zaakgerichtwerken.vng.cloud",
    },
    "LICENSE": {
        "name": "EUPL 1.2",
        "url": "https://opensource.org/licenses/EUPL-1.2",
    },
    "SERVERS": [{"url": "/api/v1/"}],
}

VNG_COMPONENTS_BRANCH = "master"
