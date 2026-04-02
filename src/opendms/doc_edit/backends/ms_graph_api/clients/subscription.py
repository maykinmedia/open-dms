import datetime
from typing import Literal

import structlog

from ..types.subscription import (
    Subscription,
    SubscriptionCollection,
)
from .base import GraphClient

logger = structlog.stdlib.get_logger(__name__)

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
AUTHORITY = f"https://login.microsoftonline.com/{settings.MS_TENANT_ID}"

SCOPES = ["Files.ReadWrite"]


class SubscriptionClient(GraphClient):
    def list_subscriptions(self) -> SubscriptionCollection:
        """
        Retrieves a collection of all subscriptions available in the system.

        This method communicates with the backend API to fetch subscription data
        and returns it as a `SubscriptionCollection` object.

        :return: A collection of subscriptions.
        """
        logger.debug("Listing subscriptions")
        return self._get("/subscriptions")

    def create_subscription(
        self,
        webhook_url: str,
        resource: str = "/me/drive/root",
        *,
        change_type: Literal["created", "updated", "deleted"],
        expiration_minutes=60,
        client_state: str | None = None,
    ) -> Subscription:
        """
        Creates a subscription to monitor changes in a specified resource. The resource
        could be a folder, a file, or any other supported entity. The subscription is valid
        until the specified expiration time and must be renewed before it expires.

        :param webhook_url: The URL that will receive notifications when the specified
            changes occur in the resource.
        :param resource: The path to the resource to monitor. Defaults to '/me/drive/root'.
        :param change_type: The type of change to monitor. Must be one of 'created',
            'updated', or 'deleted'.
        :param expiration_minutes: The duration, in minutes, after which the subscription
            expires. Defaults to 60 minutes.
        :param client_state: Optional string used to verify notifications. If provided, it
            is included in each notification for validation purposes.
        :return: An instance of `Subscription` representing the created subscription.
        """
        expiration = (
            datetime.datetime.now(datetime.UTC)
            + datetime.timedelta(minutes=expiration_minutes)
        ).isoformat()

        logger.debug(
            "Creating subscription for %s events on %s to: %s",
            change_type,
            resource,
            webhook_url,
        )
        subscription: Subscription = self._post(
            "/subscriptions",
            json={
                "changeType": change_type,
                "notificationUrl": webhook_url,
                "resource": resource,
                "expirationDateTime": expiration,
                "clientState": client_state,
            },
        )
        logger.debug("Created subscription %s", subscription["id"])
        return subscription

    def renew_subscription(
        self,
        subscription: Subscription,
        expiration_minutes: int = 60,
        client_state: str | None = None,
    ) -> Subscription:
        """
        Renews a given subscription by extending its expiration time.

        This method updates the expiration time of a subscription by a specified
        number of minutes. It calculates the new expiration time starting from the
        current time and sends a request to update the subscription's expiration
        date. The operation is useful for keeping a subscription active for longer.

        :param subscription: The subscription object to be renewed. It must include
            the subscription ID as part of its data.
        :param expiration_minutes: The number of minutes by which to extend the
            subscription's expiration. Defaults to 60 minutes if not specified.
        :return: The updated subscription object with the newly applied expiration
            time.
        """
        now = datetime.datetime.now(datetime.UTC)
        new_expiry = (now + datetime.timedelta(minutes=expiration_minutes)).isoformat()
        payload = {"expirationDateTime": new_expiry}
        if client_state is not None:
            payload["clientState"] = client_state

        logger.debug("Renewing subscription for: %s", subscription["id"])
        subscription: Subscription = self._patch(
            f"/subscriptions/{subscription['id']}",
            json=payload,
        )
        logger.debug(
            "Updated subscription %s, new expiration time: %s",
            subscription["id"],
            new_expiry,
        )
        return subscription

    def is_expiring(
        self, subscription: Subscription, minutes_threshold: int = 10
    ) -> bool:
        """
        Determine if a subscription is close to expiring.

        This method checks whether a subscription is nearing its expiration time
        based on a specified threshold in minutes. It compares the current time
        with the subscription's expiration time and returns a boolean value indicating
        whether the subscription is near expiration.

        :param subscription: The subscription object containing an expiration date in
            ISO 8601 format under the key "expirationDateTime".
        :param minutes_threshold: The number of minutes within which a subscription is
            considered close to expiring. Defaults to 10 minutes if not specified.
        :return: A boolean indicating if the subscription is within the threshold of
            expiration time.
        """
        now = datetime.datetime.now(datetime.UTC)
        expiry = datetime.datetime.fromisoformat(subscription["expirationDateTime"])
        if expiry - now <= datetime.timedelta(minutes=minutes_threshold):
            return True
        return False
