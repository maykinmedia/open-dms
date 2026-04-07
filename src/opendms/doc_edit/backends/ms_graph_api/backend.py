import base64
import mimetypes
import os
import secrets

from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.dateparse import parse_datetime

import structlog
from msal import ConfidentialClientApplication
from requests import HTTPError
from rest_framework.request import Request
from rest_framework.response import Response

from opendms.doc_edit.abstract.backend import DocumentEditBackend
from opendms.doc_edit.backends.ms_graph_api.clients.one_drive import OneDriveClient
from opendms.doc_edit.backends.ms_graph_api.clients.subscription import (
    SubscriptionClient,
)
from opendms.doc_edit.backends.ms_graph_api.types.backend import SubscriptionMeta
from opendms.doc_edit.backends.ms_graph_api.types.one_drive import DriveItem
from opendms.doc_edit.backends.ms_graph_api.types.subscription import (
    Subscription,
    SubscriptionItem,
    SubscriptionItemCollection,
)

from .models import GraphSubscription

SUBSCRIPTION_CACHE_PREFIX = "subscription_meta"
logger = structlog.stdlib.get_logger(__name__)


SCOPES = ["Files.ReadWrite"]


class MsGraphApiBackend(DocumentEditBackend):
    def __init__(self):
        self.one_drive_client = OneDriveClient()
        self.subscription_client = SubscriptionClient()

    def authenticate(self, request: Request, redirect_url: str | None = None):
        """
        Begin the OAuth2 PKCE authentication flow.

        :param request: Django request object
        :param redirect_url: URL to redirect to after login
        :return: Django redirect response to Microsoft login
        """
        app_msal = self._build_msal_app()
        auth_flow = app_msal.initiate_auth_code_flow(SCOPES, redirect_uri=redirect_url)

        request.session["auth_flow"] = auth_flow
        return redirect(auth_flow["auth_uri"])

    def authenticated_callback(self, request: Request) -> dict:
        """
        Complete the PKCE authentication flow using the code in request.GET.

        :param request: Django request object
        :return: dict with access token and authentication result
        """
        auth_flow = request.session.get("auth_flow")
        if not auth_flow:
            raise ValueError("Authentication flow not initialized in session.")

        app_msal = self._build_msal_app()
        result = app_msal.acquire_token_by_auth_code_flow(auth_flow, request.GET)

        request.session.pop("auth_flow", None)
        token = result["access_token"]
        if not token:
            raise ValueError(result.get("error_description", "Authentication failed."))

        self._set_token(token)

        request.session["access_token"] = token
        return result

    def open(self, file_path: str) -> str:
        """
        Start a process to access or edit a file.

        This implementation uploads the file to a dedicated OneDrive folder,
        ensures a change subscription is active, and redirects the user to the
        Microsoft-hosted editor for the uploaded file.

        :param file_path: Identifier or path of the target file.
        :return: A response that continues the file access/edit flow.
        :raises BlockingIOError: If the file cannot be accessed at this time.
        """

        with open(file_path, "rb") as f:
            file_name = os.path.basename(file_path)

            folder = self._ensure_sync_folder()
            folder_id = folder["id"]

            try:
                drive_item = self.one_drive_client.upload_item(
                    file_name,
                    f,
                    self._get_mime_type(file_path),
                    parent_item_id=folder_id,
                )

                # TODO FIX to save file info
                # TODO remove or replace with cache
                """
                with shelve.open("file_map") as file_id_mapping:
                    file_id_mapping[drive_item["id"]] = file_path
                """

            except HTTPError as error:
                if error.response.status_code == 423:
                    raise BlockingIOError("The file could not be opened")
                raise error

        self._ensure_subscription()
        return self.one_drive_client.get_item_link(item_id=drive_item["id"])

    def updated_callback(self, request) -> Response:
        validation_token = request.GET.get("validationToken")
        if validation_token:
            return Response(validation_token, status=200, content_type="text/plain")

        data: SubscriptionItemCollection = request.data or {}
        notifications = data.get("value")

        result: tuple[GraphSubscription, SubscriptionItem] | None = None

        logger.info("notifications")
        logger.info(notifications)
        logger.info("notifications")
        for notification in notifications:
            try:
                subscription = GraphSubscription.objects.get(
                    subscription_id=notification["subscription_id"]
                )
                result = (subscription, notification)
                break
            except GraphSubscription.DoesNotExist:
                continue

        if not result:
            logger.error("Unknown subscription")
            return Response(
                "Unknown subscription", status=400, content_type="text/plain"
            )

        subscription, notification = result

        if subscription.client_state != notification["client_state"]:
            logger.error("Invalid clientState")
            return Response(
                "Invalid clientState", status=400, content_type="text/plain"
            )

        subscription_meta = {
            "client_state": subscription.client_state,
            "delta_url": subscription.delta_url,
            "expiration": subscription.expiration_date_time,
            "token": subscription.token,
        }

        self._sync_updated_files(subscription_meta)

        return Response(status=204, content_type="text/plain")

    #
    # Private API.
    #

    def _set_token(self, token: str) -> None:
        self.one_drive_client.token = token
        self.subscription_client.token = token

    def _build_msal_app(self) -> ConfidentialClientApplication:
        """
        Builds and returns an instance of the ConfidentialClientApplication.

        This function initializes and configures an MSAL ConfidentialClientApplication
        used for handling authentication against Azure Active Directory. The client
        application is initialized with a specified client ID, authority, and client
        secret.

        Required Microsoft Graph permission: Files.ReadWrite

        :return: An instance of ConfidentialClientApplication configured with the given
            credentials.
        """
        return ConfidentialClientApplication(
            settings.MSGRAPH_API_BACKEND_CLIENT_ID,
            authority=f"https://login.microsoftonline.com/{settings.MSGRAPH_API_BACKEND_TENANT_ID}",
            client_credential=settings.MSGRAPH_API_BACKEND_CLIENT_SECRET,
        )

    # TODO test this folder, env var folder?
    def _ensure_sync_folder(self) -> DriveItem:
        """
        Ensures the existence of MSGRAPH_API_BACKEND_SYNC_FOLDER in the user's OneDrive.
        If the folder does not already exist, it will be created.

        :param token: The OAuth2 token used for authentication with the Microsoft Graph API.

        :return: The unique identifier (ID) of the sync folder in OneDrive.
        """
        drive_items = self.one_drive_client.list_children().get("value")
        for item in drive_items:
            if item["name"] == settings.MSGRAPH_API_BACKEND_SYNC_FOLDER and item.get(
                "folder"
            ):
                return item

        return self.one_drive_client.create_item(
            settings.MSGRAPH_API_BACKEND_SYNC_FOLDER, folder=True
        )

    def _ensure_subscription(self) -> Subscription:
        data = self.subscription_client.list_subscriptions()
        subscriptions: list[Subscription] = data["value"]
        webhook_url = reverse("webhook")

        for subscription in subscriptions:
            if (
                not subscription["notificationUrl"].endswith(webhook_url)
                or subscription["resource"] != "/me/drive/root"
            ):
                continue

            subscription_id = subscription["id"]

            if self.subscription_client.is_expiring(subscription):
                client_state = self._create_client_state_secret()

                self.subscription_client.renew_subscription(
                    subscription, client_state=client_state
                )

                GraphSubscription.objects.update_or_create(
                    subscription_id=subscription_id,
                    defaults={
                        "client_state": client_state,
                        "resource": subscription["resource"],
                        "notification_url": subscription["notificationUrl"],
                        "expiration_date_time": parse_datetime(
                            subscription["expirationDateTime"]
                        ),
                        "delta_url": "",
                        "token": self.subscription_client.token,
                    },
                )

            return subscription

        client_state = self._create_client_state_secret()
        subscription = self.subscription_client.create_subscription(
            webhook_url,
            change_type="updated",
            resource="/me/drive/root",
            client_state=client_state,
        )

        subscription_id = subscription["id"]

        GraphSubscription.objects.update_or_create(
            subscription_id=subscription_id,
            defaults={
                "client_state": client_state,
                "resource": subscription["resource"],
                "notification_url": subscription["notificationUrl"],
                "expiration_date_time": parse_datetime(
                    subscription["expirationDateTime"]
                ),
                "delta_url": "",
                "token": self.subscription_client.token,
            },
        )
        return subscription

    def _get_mime_type(self, file_path: str) -> str:
        """
        Return the MIME type for a given file based on its extension.
        """
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or "application/octet-stream"

    def _create_client_state_secret(self):
        """
        Generate a secure random client state secret.
        """
        random_bytes = secrets.token_bytes(64)
        return base64.urlsafe_b64encode(random_bytes).rstrip(b"=").decode("utf-8")

    def _sync_updated_files(self, subscription_meta: SubscriptionMeta):
        delta = self.one_drive_client.get_delta(subscription_meta["delta_url"])
        subscription_meta["delta_url"] = delta.get("@odata.deltaLink")
        deltas = delta["value"]

        if not deltas:
            return
        """
        with shelve.open("file_map") as file_id_mapping:
            for item in deltas:
                item_id = item["id"]
                file_path = file_id_mapping.get(item["id"])

                if file_path:
                    self._download_file(item_id, file_path)
        """
        for item in deltas:
            item_id = item["id"]
            if "file" in item:
                self._download_file(item_id, "tmp/test.txt")

    def _download_file(self: str, item_id: str, file_path: str):
        response = self.one_drive_client.download_item(item_id=item_id)
        file_name = os.path.basename(file_path)
        if response.status_code == 200:
            with open(file_name, "wb") as f:
                f.write(response.content)
