from .documenten import get_documenten_client
from .zaaktypen import get_zaaktypen_client
from .zaken import get_zaken_client

__all__ = [
    "get_zaaktypen_client",
    "get_zaken_client",
    "get_documenten_client",
]
