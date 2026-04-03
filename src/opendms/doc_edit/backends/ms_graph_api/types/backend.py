from typing import TypedDict

from ..clients.subscription import Subscription


class SubscriptionMeta(TypedDict):
    client_state: str
    delta_url: str | None
    expiration: str
    subscription: Subscription
    token: str
