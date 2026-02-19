import os

os.environ["_USE_STRUCTLOG"] = "True"

from functools import partial

from django.utils.functional import SimpleLazyObject

from pathlib import Path

from maykin_common.health_checks import default_health_check_apps
from open_api_framework.conf.base import *  # noqa
from self_certifi import EXTRA_CERTS_ENVVAR as _EXTRA_CERTS_ENVVAR

from .utils import load_indexable_file_types
from open_api_framework.conf.utils import config  # noqa

from .api import *  # noqa

# APPLICATIONS enabled for this project
#
INSTALLED_APPS = INSTALLED_APPS + [
    *default_health_check_apps,
    # External applications.
    "hijack",
    "hijack.contrib.admin",
    "maykin_common",
    # Project applications.
    "opendms.accounts",
    "opendms.api",
    "opendms.utils",
    "opendms.frontend",
]

# Additional locations of static files
STATICFILES_DIRS += [Path(DJANGO_PROJECT_DIR) / "frontend/dist/static"]

#
# SECURITY settings
#
CSRF_FAILURE_VIEW = "maykin_common.views.csrf_failure"

#
# Custom settings
#
PROJECT_NAME = "Open DMS"

# Displaying environment information
ENVIRONMENT_LABEL = config(
    "ENVIRONMENT_LABEL",
    default=ENVIRONMENT,
    add_to_docs=False,
)
ENVIRONMENT_BACKGROUND_COLOR = config(
    "ENVIRONMENT_BACKGROUND_COLOR",
    default="orange",
    add_to_docs=False,
)
ENVIRONMENT_FOREGROUND_COLOR = config(
    "ENVIRONMENT_FOREGROUND_COLOR",
    default="black",
    add_to_docs=False,
)
SHOW_ENVIRONMENT = config(
    "SHOW_ENVIRONMENT",
    default=True,
    add_to_docs=False,
)

# This setting is used by the csrf_failure view (accounts app).
# You can specify any path that should match the request.path
# Note: the LOGIN_URL Django setting is not used because you could have
# multiple login urls defined.
LOGIN_URLS = [reverse_lazy("admin:login")]


# Default (connection timeout, read timeout) for the requests library (in seconds)
REQUESTS_DEFAULT_TIMEOUT = (10, 30)

##############################
#                            #
# 3RD PARTY LIBRARY SETTINGS #
#                            #
##############################

#
# Django-Admin-Index
#
ADMIN_INDEX_SHOW_REMAINING_APPS = False
ADMIN_INDEX_SHOW_REMAINING_APPS_TO_SUPERUSERS = True
ADMIN_INDEX_DISPLAY_DROP_DOWN_MENU_CONDITION_FUNCTION = (
    "maykin_common.django_two_factor_auth.should_display_dropdown_menu"
)


#
# DJANGO-HIJACK
#
HIJACK_PERMISSION_CHECK = "maykin_2fa.hijack.superusers_only_and_is_verified"
HIJACK_INSERT_BEFORE = (
    '<div class="content">'  # note that this only applies to the admin
)

#
# DJANGO REST FRAMEWORK
#

ENABLE_THROTTLING = config(
    "ENABLE_THROTTLING",
    default=True,
    add_to_docs=False,
)
throttle_rate_anon = (
    config(
        "THROTTLE_RATE_ANON",
        default="2500/hour",
        add_to_docs=False,
    )
    if ENABLE_THROTTLING
    else None
)
throttle_rate_user = (
    config(
        "THROTTLE_RATE_USER",
        default="15000/hour",
        add_to_docs=False,
    )
    if ENABLE_THROTTLING
    else None
)

REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = (
    "rest_framework.throttling.AnonRateThrottle",
    "rest_framework.throttling.UserRateThrottle",
    "rest_framework.throttling.ScopedRateThrottle",
)
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
    # used by regular throttle classes
    "anon": throttle_rate_anon,
    "user": throttle_rate_user,
}

TEMPLATES[0]["DIRS"] += [DJANGO_PROJECT_DIR / "frontend/dist"]


#
# Elasticsearch DSL custom settings
#
SEARCH_INDEX = {
    "HOST": config(  # pyright: ignore[reportCallIssue]
        "ELASTICSEARCH_HOST",
        default="",
        group="Elastic Search",
        help_text="Host where the ES cluster is deployed, e.g. https://es.example.com:9200",
    ),
    "USER": config(  # pyright: ignore[reportCallIssue]
        "ELASTICSEARCH_USER",
        default="",
        group="Elastic Search",
        help_text="Username for ES authentication.",
    ),
    "PASSWORD": config(  # pyright: ignore[reportCallIssue]
        "ELASTICSEARCH_PASSWORD",
        default="",
        group="Elastic Search",
        help_text="Password for ES authentication.",
    ),
    "TIMEOUT": config(  # pyright: ignore[reportCallIssue]
        "ELASTICSEARCH_TIMEOUT",
        default=60,
        group="Elastic Search",
        help_text="HTTP timeout for ES API interactions.",
    ),
    "CA_CERTS": config(  # pyright: ignore[reportCallIssue]
        "ELASTICSEARCH_CA_CERTS",
        default="",
        group="Elastic Search",
        help_text=(
            "Path to CA bundle (in PEM) format if self-signed certificates or "
            "a private CA are used to connect to the ES cluster. Alternatively, "
            f"if {_EXTRA_CERTS_ENVVAR} is defined, it will be used."
        ),
    ),
    # https://www.elastic.co/guide/en/elasticsearch/reference/current/docs-refresh.html
    "REFRESH": config(  # pyright: ignore[reportCallIssue]
        "ELASTICSEARCH_REFRESH",
        default=False,
        group="Elastic Search",
        help_text=(
            "Refresh control for ES index, update, delete and bulk APIs. In "
            "production, you should leave this to the default of 'false'."
        ),
    ),
    "INDEXED_CHARS": config(  # pyright: ignore[reportCallIssue]
        "ELASTICSEARCH_INDEXED_CHARS",
        default=100000,
        group="Elastic Search",
        help_text=(
            "Attachment processor number of chars being used for "
            "extraction to prevent huge fields.\n\n"
            "  - Use `-1` for no limit.\n"
            "  - default and max `100000`.\n\n"
        ),
    ),
    "MAX_INDEX_FILE_SIZE": config(  # pyright: ignore[reportCallIssue]
        "ELASTICSEARCH_MAX_INDEX_FILE_SIZE",
        default=99 / 1.33 * 1000 * 1000,  # 99mb (not mib)
        group="Elastic Search",
        help_text=(
            "The maximum file size (in bytes) that leads to full text indexing of the "
            "file content. For files larger than this limit, only the metadata is "
            "indexed. Keep in mind that Elastic Search must be configured "
            "appropriately to allow sufficiently large HTTP request body sizes."
        ),
    ),
}

SEARCH_INDEXABLE_FILE_TYPES = SimpleLazyObject(
    partial(load_indexable_file_types, BASE_DIR)
)
