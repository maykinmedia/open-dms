import os

os.environ["_USE_STRUCTLOG"] = "True"

from pathlib import Path

from maykin_common.health_checks import default_health_check_apps
from open_api_framework.conf.base import *  # noqa
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
