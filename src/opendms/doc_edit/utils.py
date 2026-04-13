from datetime import datetime

from django.utils import timezone


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
