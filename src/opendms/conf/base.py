import os

os.environ["_USE_STRUCTLOG"] = "True"

from functools import partial
from pathlib import Path

from django.utils.functional import SimpleLazyObject

from celery.schedules import crontab
from maykin_common.health_checks import default_health_check_apps
from open_api_framework.conf.base import *  # noqa
from open_api_framework.conf.utils import config  # noqa
from self_certifi import EXTRA_CERTS_ENVVAR as _EXTRA_CERTS_ENVVAR

from .api import *  # noqa
from .utils import load_indexable_file_types

# APPLICATIONS enabled for this project
#
INSTALLED_APPS = INSTALLED_APPS + [
    *default_health_check_apps,
    "django.contrib.postgres",
    # External applications.
    "hijack",
    "hijack.contrib.admin",
    "maykin_common",
    "django_celery_beat",
    # Project applications.
    "opendms.accounts",
    "opendms.api",
    "opendms.search_index",
    "opendms.doc_edit",
    "opendms.utils",
    "opendms.frontend",
]

# Additional locations of static files
STATICFILES_DIRS += [Path(DJANGO_PROJECT_DIR) / "frontend/dist/static"]

#
# SECURITY settings
#
CSRF_FAILURE_VIEW = "maykin_common.views.csrf_failure"


FRONTEND_ORIGIN = config(
    "FRONTEND_ORIGIN",
    default="http://localhost:5173",
    help_text="Origin for the frontend application, this gets added to CSRF_TRUSTED_ORIGINS",
)
CSRF_TRUSTED_ORIGINS = CSRF_TRUSTED_ORIGINS + [FRONTEND_ORIGIN]

# Development reads CSRF cookie instead of hidden input due to lack of template processing
CSRF_COOKIE_HTTPONLY = not DEBUG

CSRF_COOKIE_SECURE = not DEBUG

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
# Django setup configuration
#
SETUP_CONFIGURATION_STEPS = (
    "zgw_consumers.contrib.setup_configuration.steps.ServiceConfigurationStep",
    "opendms.api.setup_configuration.steps.ZGWApiConfigurationStep",
)


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
    "ANALYZER": config(  # pyright: ignore[reportCallIssue]
        "ELASTICSEARCH_ANALYZER",
        default="dutch",
        group="Elastic Search",
        help_text="Default analyzer to use for text fields in Elasticsearch mappings.",
    ),
}
REQUESTS_CA_BUNDLE = config(
    "REQUESTS_CA_BUNDLE",
    default=None,
    group="Elastic Search",
    help_text=(
        "Path to a CA bundle file (PEM format) used to verify HTTPS requests. "
        "This is used as a fallback if ELASTICSEARCH_CA_CERTS is not provided. "
        "Useful when connecting to services secured with a private or self-signed CA."
    ),
)
SEARCH_INDEXABLE_FILE_TYPES = SimpleLazyObject(
    partial(load_indexable_file_types, BASE_DIR)
)


#
# CELERY - async task queue
#
# CELERY_BROKER_URL  defined in open-api-framework
# CELERY_RESULT_BACKEND  defined in open-api-framework

# Add (by default) 1 (soft), 5 (hard) minute timeouts to all Celery tasks.
CELERY_TASK_TIME_LIMIT = config(
    "CELERY_TASK_HARD_TIME_LIMIT",
    default=5 * 60,
    help_text="Hard timeout for Celery tasks in seconds",
)  # hard
CELERY_TASK_SOFT_TIME_LIMIT = config(
    "CELERY_TASK_SOFT_TIME_LIMIT",
    default=1 * 60,
    help_text="Soft timeout for Celery tasks in seconds",
)  # soft

CELERY_BEAT_SCHEDULE = {
    "update_documents_hourly": {
        "task": "opendms.search_index.document_task.index_all_documents",
        "schedule": crontab(minute=0),
    },
    "update_zaken_hourly": {
        "task": "opendms.search_index.zaak_task.index_all_zaken",
        "schedule": crontab(minute=5),
    },
}

# Only ACK when the task has been executed. This prevents tasks from getting lost, with
# the drawback that tasks should be idempotent (if they execute partially, the mutations
# executed will be executed again!)
CELERY_TASK_ACKS_LATE = True

# ensure that no tasks are scheduled to a worker that may be running a very long-running
# operation, leading to idle workers and backed-up workers. The `-O fair` option
# *should* have the same effect...
CELERY_WORKER_PREFETCH_MULTIPLIER = 1

#
# Microsoft Entra ID App Configuration
#
MSGRAPH_API_BACKEND_TENANT_ID = config(
    "MSGRAPH_API_BACKEND_TENANT_ID",
    None,
    group="Microsoft configuration",
    help_text="The Azure Entra ID tenant (directory) ID used by MsGraphApiBackend.",
)

MSGRAPH_API_BACKEND_CLIENT_ID = config(
    "MSGRAPH_API_BACKEND_CLIENT_ID",
    None,
    group="Microsoft configuration",
    help_text="The Application (client) ID registered for MsGraphApiBackend in Entra ID.",
)

MSGRAPH_API_BACKEND_CLIENT_SECRET = config(
    "MSGRAPH_API_BACKEND_CLIENT_SECRET",
    None,
    group="Microsoft configuration",
    help_text="The client secret used by MsGraphApiBackend to authenticate against Microsoft Graph API.",
)

MSGRAPH_API_BACKEND_SYNC_FOLDER = config(
    "MSGRAPH_API_BACKEND_SYNC_FOLDER",
    default="ODS_SYNC",
    group="Microsoft configuration",
    help_text="The folder where MsGraphApiBackend syncs data.",
)

MSGRAPH_API_BACKEND_WEBHOOK_NOTIFICATION_URL = config(
    "MSGRAPH_API_BACKEND_WEBHOOK_NOTIFICATION_URL",
    default=None,
    group="Microsoft configuration",
    help_text="The callback notification URL to use for subscription webhooks.",
)
