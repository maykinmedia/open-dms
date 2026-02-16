import os
import warnings

os.environ.setdefault("DEBUG", "yes")
os.environ.setdefault("ALLOWED_HOSTS", "*")
os.environ.setdefault(
    "SECRET_KEY",
    "django-insecure-kex=ipoau_q(o_w=6bd8q6_sb2#xgkdbknq4m&hl2jtx(7#$n_",
)
os.environ.setdefault("IS_HTTPS", "no")
os.environ.setdefault("VERSION_TAG", "dev")

os.environ.setdefault("DB_NAME", "opendrc")
os.environ.setdefault("DB_USER", "opendrc")
os.environ.setdefault("DB_PASSWORD", "opendrc")

os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")

from .base import *  # noqa isort:skip
from .base import CACHES

CACHES.update(
    {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "default",
        },
        # See: https://github.com/jazzband/django-axes/blob/master/docs/configuration.rst#cache-problems
        "axes": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"},
    }
)

ENVIRONMENT = "CI"


#
# Django-axes
#
AXES_BEHIND_REVERSE_PROXY = False


# THOU SHALT NOT USE NAIVE DATETIMES
warnings.filterwarnings(
    "error",
    r"DateTimeField .* received a naive datetime",
    RuntimeWarning,
    r"django\.db\.models\.fields",
)
