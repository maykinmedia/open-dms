from typing import TypedDict

from backends.ms_graph_api.types.subscription import Subscription


class SubscriptionMeta(TypedDict):
    client_state: str
    delta_url: str | None
    expiration: str
    subscription: Subscription
    token: str
