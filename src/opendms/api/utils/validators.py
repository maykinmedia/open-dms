import re
from uuid import UUID


def extract_uuid(url: str) -> str | None:
    match = re.search(
        r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
        url,
    )
    if match:
        uuid_str = match.group(0)
        try:
            UUID(uuid_str)
            return uuid_str
        except ValueError:
            return None
    return None
