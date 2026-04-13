import base64
import mimetypes
import secrets

from django.conf import settings
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.dateparse import parse_datetime

import structlog
from msal import ConfidentialClientApplication
from requests import HTTPError
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response

from opendms.doc_edit.abstract.backend import DocumentEditBackend
from opendms.doc_edit.backends.ms_graph_api.clients.one_drive import OneDriveClient
from opendms.doc_edit.backends.ms_graph_api.clients.subscription import (
    SubscriptionClient,
)
from opendms.doc_edit.backends.ms_graph_api.types.one_drive import DriveItem
from opendms.doc_edit.backends.ms_graph_api.types.subscription import (
    Subscription,
    SubscriptionItem,
    SubscriptionItemCollection,
)
from opendms.doc_edit.models import BaseDriveDocument, BaseDriveSubscription
from opendms.doc_edit.utils import is_within_threshold

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

    def _set_token(self, token: str) -> None:
        self.one_drive_client.token = token
        self.subscription_client.token = token

    def open(self, file_path: str, file_uuid: str, file_ext: str) -> str:
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
            folder = self._ensure_sync_folder()
            folder_id = folder["id"]
            file_name = f"{file_uuid}{file_ext}"
            try:
                drive_item = self.one_drive_client.upload_item(
                    file_name,
                    f,
                    self._get_mime_type(file_path),
                    parent_item_id=folder_id,
                )
            except HTTPError as error:
                logger.exception("error_file_could_not_be_opened")
                raise error

        document_drive_id = drive_item["id"]

        # create instance to check the status of the document
        BaseDriveDocument.objects.update_or_create(
            document_uuid=file_uuid,
            defaults={
                "document_drive_id": document_drive_id,
                "document_extension": file_ext,
            },
        )

        self._ensure_subscription()
        return self.one_drive_client.get_item_link(item_id=document_drive_id)

    def updated_callback(self, request) -> Response:
        validation_token = request.GET.get("validationToken")
        if validation_token:
            return Response(
                validation_token, status=status.HTTP_200_OK, content_type="text/plain"
            )

        data: SubscriptionItemCollection = request.data or {}
        notifications = data.get("value", [])

        result: tuple[BaseDriveSubscription, SubscriptionItem] | None = None

        for notification in notifications:
            try:
                subscription = BaseDriveSubscription.objects.get(
                    subscription_id=notification["subscription_id"]
                )
                result = (subscription, notification)
                break
            except BaseDriveSubscription.DoesNotExist:
                continue

        if not result:
            logger.warning("no_subscriptions_saved", notifications=notifications)
            return Response(
                "Unknown subscription",
                status=status.HTTP_400_BAD_REQUEST,
                content_type="text/plain",
            )

        subscription, notification = result

        if subscription.client_state != notification["client_state"]:
            logger.error("client_state_not_valid")
            return Response(
                "Invalid clientState",
                status=status.HTTP_400_BAD_REQUEST,
                content_type="text/plain",
            )

        self._sync_updated_files(subscription)
        return Response(status=204)

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

    # TODO create endpoint -> /sync to update/run _ensure_subscription method
    def _ensure_subscription(self) -> Subscription:
        """
        Ensure an active subscription exists by checking the current subscriptions and renewing
        an existing one or creating a new subscription if necessary. This function interacts with
        a Graph API endpoint to manage subscriptions.

        :return: The current or newly created subscription.
        """

        self._cleanup_subscriptions()

        data = self.subscription_client.list_subscriptions()
        subscriptions: list[Subscription] = data["value"]
        webhook_url = settings.MSGRAPH_API_BACKEND_WEBHOOK_NOTIFICATION_URL

        if webhook_url is None:
            raise ValueError(
                "MSGRAPH_API_BACKEND_WEBHOOK_NOTIFICATION_URL is not configured!"
            )

        for subscription in subscriptions:
            if (
                not subscription["notificationUrl"].endswith(webhook_url)
                or subscription["resource"] != "/me/drive/root"
                or not BaseDriveSubscription.objects.filter(subscription_id=subscription["id"]).exists()
            ):
                logger.debug("Ignoring existing subscription %s", subscription["id"])
                continue

            subscription_id = subscription["id"]

            if self.subscription_client.is_expiring(subscription):
                client_state = self._create_client_state_secret()

                self.subscription_client.renew_subscription(
                    subscription, client_state=client_state
                )

                BaseDriveSubscription.objects.update_or_create(
                    subscription_id=subscription_id,
                    client_state=client_state,
                    defaults={
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

        logger.info("create_new_subscription")
        client_state = self._create_client_state_secret()
        subscription = self.subscription_client.create_subscription(
            webhook_url,
            change_type="updated",
            resource="/me/drive/root",  # microsoft business allow only subscriptions for this folder
            client_state=client_state,
        )
        BaseDriveSubscription.objects.update_or_create(
            subscription_id=subscription["id"],
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

    def _cleanup_subscriptions(self) -> None:
        """
        Removes expired subscriptions from the database based on the current UTC time.
        Note: this does not unsubscribe webhooks.
        """
        deleted_count, _ = BaseDriveSubscription.objects.filter(
            expiration_date_time__lt=timezone.now()
        ).delete()

        if deleted_count:
            logger.info("subscriptions_deleted")

    def _sync_updated_files(self, subscription: BaseDriveSubscription) -> None:
        self._set_token(subscription.token)

        documents = BaseDriveDocument.objects.filter(created_at__isnull=False)
        if not documents.exists():
            return

        drive_documents = self.one_drive_client.list_children(
            item_id=f"root:/{settings.MSGRAPH_API_BACKEND_SYNC_FOLDER}:"
        ).get("value", [])
        if not drive_documents:
            logger.warning("no_drive_documents_found")
            return

        drive_documents_dict = {
            doc["id"]: doc.get("fileSystemInfo", {}) for doc in drive_documents
        }

        to_update = []

        for document in documents:
            file_system_info = drive_documents_dict.get(document.document_drive_id)
            if file_system_info is None:
                # TODO decide whether to delete or disable the document
                document.created_at = None
                document.save()
                logger.exception("disable_document")
                continue

            created = parse_datetime(file_system_info.get("createdDateTime"))
            modified = parse_datetime(file_system_info.get("lastModifiedDateTime"))

            if not modified:
                logger.warning("no_update_date_for_document")
                continue

            if is_within_threshold(created, modified):
                logger.warning("new_file_not_modified")
                continue

            if not document.updated_at or document.updated_at < modified:
                document.updated_at = timezone.now()
                to_update.append(document)

        if to_update:
            # TODO improve logs, with more details
            BaseDriveDocument.objects.bulk_update(to_update, fields=["updated_at"])
            logger.info("documents_updated")
