# ruff: noqa: F403,F405
import json
from collections.abc import Callable, Sequence
from functools import lru_cache
from pathlib import Path

import structlog
from maykin_common.config import config as _config
from open_api_framework.conf.utils import config as _legacy_config
from sentry_sdk.integrations import DidNotEnable, django, redis

logger = structlog.stdlib.get_logger(__name__)


def wrap_config[T, **P](wrapped: Callable[P, T]):
    def inner(
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> T:
        help_text = kwargs.pop("help_text", "")
        group = kwargs.pop("group", "")

        # ensure the docs registration stuff is still happening
        option = args[0]
        assert isinstance(option, str)
        _legacy_kwargs = {**kwargs, "help_text": help_text, "group": group}
        _legacy_config(option, **_legacy_kwargs)  # type: ignore

        # can't handle the typing overlaods in a decorator...
        return wrapped(*args, **kwargs)

    return inner


config = wrap_config(_config)


@lru_cache(maxsize=1)
def load_indexable_file_types(base: Path) -> Sequence[str]:  # pragma: no cover
    """
    Load the JSON configuration file and extract relevant mime types.

    The shared file types configuration file documents all the supported file types
    and which of those can be indexed as full text in elastic search.
    """
    config_file = base / "filetypes" / "fileTypes.json"
    if not config_file.exists():
        logger.warning("file_does_not_exist", extra={"file": str(config_file)})
        return []

    with config_file.open() as infile:
        file_types = json.load(infile)

    return [
        file_type["mimeType"]
        for file_type in file_types
        if file_type.get("canBeIndexed")
    ]


def get_sentry_integrations() -> list:
    """
    Determine which Sentry SDK integrations to enable.
    """
    default = [
        django.DjangoIntegration(),
        redis.RedisIntegration(),
    ]
    extra = []

    try:
        from sentry_sdk.integrations import celery
    except DidNotEnable:  # happens if the celery import fails by the integration
        pass
    else:
        extra.append(celery.CeleryIntegration())

    return [*default, *extra]
