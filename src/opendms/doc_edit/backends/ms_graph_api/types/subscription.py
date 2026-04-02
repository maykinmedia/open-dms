from typing import TypedDict


class Subscription(TypedDict, total=False):
    id: str
    resource: str
    changeType: str
    clientState: str
    notificationUrl: str
    expirationDateTime: str
    applicationId: str
    creatorId: str
    latestSupportedTlsVersion: str


# Special chars
class SubscriptionCollection(TypedDict):
    value: list[Subscription]


class SubscriptionItem(TypedDict):
    resource: str
    changeType: str
    subscriptionId: str
    clientState: str
    tenantId: str
    resourceData: dict
    subscriptionExpirationDateTime: str


class SubscriptionItemCollection(TypedDict):
    value: list[SubscriptionItem]
