from datetime import datetime

from django.utils import timezone

import structlog
from requests import HTTPError

logger = structlog.stdlib.get_logger(__name__)


def handle_exception(exception: Exception, default_message: str = "Unknown error"):
    """
    Handles exceptions raised during HTTP requests or other operations.

    This method processes specific known exception types and raises appropriate
    custom exceptions with detailed error messages. If the exception does not
    match any of the predefined types, it raises a generic IOError.

    Parameters:
      exception (Exception): The exception that occurred during the operation.
      default_message (str, optional): A default error message to use when no additional
        details are available. Defaults to "Unknown error".

    Raises:
      PermissionError: Raised when the exception is identified as an HTTPError and
        has an error response indicating insufficient permissions or authentication
        failure.
      IOError: Raised for all other types of exceptions with an additional context
        about inability to process the operation.
    """
    if getattr(exception, "response", None):
        logger.debug(exception.response.text)

    if isinstance(exception, HTTPError):
        try:
            data = exception.response.json()
            message = data["error"]["message"]
            raise PermissionError(message) from exception
        except Exception:
            raise PermissionError("Authentication failed.") from exception

    raise OSError(default_message) from exception


def is_within_threshold(
    dt1: datetime,
    dt2: datetime,
    threshold_seconds: int = 15,
) -> bool:
    """
    Returns True if two datetimes are within the given threshold of each other.

    :param dt1: First datetime.
    :param dt2: Second datetime.
    :param threshold_seconds: Maximum allowed difference in seconds. Defaults to 15.
    :return: True if the difference is within the threshold, False otherwise.
    """
    return abs(dt1 - dt2) <= timezone.timedelta(seconds=threshold_seconds)
