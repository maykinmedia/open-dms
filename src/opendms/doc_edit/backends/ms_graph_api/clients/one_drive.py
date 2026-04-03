from typing import BinaryIO

import structlog
from rest_framework.response import Response

from opendms.doc_edit.backends.ms_graph_api.types.one_drive import (
    DriveItem,
    DriveItemCollection,
    DriveItemDelta,
)

from .base import GraphClient

logger = structlog.stdlib.get_logger(__name__)


class OneDriveClient(GraphClient):
    def create_item(
        self,
        name: str,
        folder: bool = True,
        additional_props: dict = None,
        *,
        drive_id: str | None = None,
        group_id: str | None = None,
        site_id: str | None = None,
        user_id: str | None = None,
        parent_item_id: str = "root",
    ) -> DriveItem:
        """
        Creates an item in the specified location within a drive. The item can be created
        as either a folder or a non-folder file. Additional properties can be included
        to customize the item further.

        :param name: The name of the item to be created.
        :param folder: Indicates if the item should be created as a folder. Defaults to True.
        :param additional_props: A dictionary of additional properties to be included in the item.
        :param drive_id: The unique identifier of the drive where the item will be created.
        :param group_id: The unique identifier of the group where the drive is located.
        :param site_id: The unique identifier of the site where the drive is located.
        :param user_id: The unique identifier of the user who owns the drive.
        :param parent_item_id: The unique identifier of the parent item under which
            the new item will be created. Defaults to "root".
        :return: The created DriveItem object.
        """
        url = self._get_children_url(
            drive_id=drive_id,
            group_id=group_id,
            site_id=site_id,
            user_id=user_id,
            item_id=parent_item_id,
        )

        payload: DriveItem = {"name": name}
        if folder:
            payload["folder"] = {}
        else:
            payload["file"] = {}  # non-folder item

        if additional_props:
            payload.update(additional_props)

        logger.debug("Creating %s: %s", "folder" if folder else "file", name)
        drive_item: DriveItem = self._post(url, payload)
        logger.debug("Created %s: %s", "folder" if folder else "file", drive_item["id"])
        return drive_item

    def download_item(
        self,
        *,
        drive_id: str | None = None,
        group_id: str | None = None,
        site_id: str | None = None,
        user_id: str | None = None,
        item_id: str = "root",
    ) -> Response:
        """
        Downloads an item from a specific location within a drive, site, group, or user context
        and returns the raw response. The method constructs a content URL based on the specified
        parameters and initiates a GET request to retrieve the item.

        :param drive_id: The unique identifier of the drive. Optional.
        :param group_id: The unique identifier of the group. Optional.
        :param site_id: The unique identifier of the site. Optional.
        :param user_id: The unique identifier of the user. Optional.
        :param item_id: The unique identifier of the item to download. Defaults to "root".
        :return: A ``Response`` object containing the raw data of the downloaded item.
        """
        item_url = self._get_item_url(
            drive_id=drive_id,
            group_id=group_id,
            site_id=site_id,
            user_id=user_id,
            item_id=item_id,
        )
        logger.debug("Downloading item: %s", item_url)
        return self._request("GET", f"{item_url}/content", raw_response=True)

    def upload_item(
        self,
        filename: str,
        content: bytes | BinaryIO,
        content_type: str,
        *,
        drive_id: str | None = None,
        group_id: str | None = None,
        site_id: str | None = None,
        user_id: str | None = None,
        parent_item_id: str = "root",
    ) -> DriveItem:
        """
        Uploads an item to the specified drive or directory in the system. This function is designed to
        send binary data to a storage location specified by the user. It can upload files to different
        contexts, such as drives linked to groups, users, or SharePoint sites, by adapting the target
        resource URL accordingly.

        :param filename: Name of the file to be uploaded, including its extension.
        :param content: File content to upload, represented as a byte stream.
        :param content_type: MIME type of the file, indicating the nature and format of the content.
        :param drive_id: Optional identifier for the target drive where the file should be uploaded.
                         Defaults to None if the drive is not specified explicitly.
                         Example: 'drive-id-12345'
        :param group_id: Optional identifier for a group drive. This is used when uploading
                         within the scope of a specific group. Defaults to None if not applicable.
                         Example: 'group-id-54321'
        :param site_id: Optional identifier for a SharePoint site. This is useful in scenarios where
                        the file needs to be uploaded into a site's library. Defaults to None if not applicable.
                        Example: 'site-id-abc123'
        :param user_id: Optional identifier for a user's drive. When provided, the file will be uploaded
                        to a drive associated with the specified user. Defaults to None if not applicable.
                        Example: 'user-id-xyz456'
        :param parent_item_id: Identifier for the parent folder where the file will be uploaded.
                               Defaults to "root", referencing the root directory of the target.
                               Example: 'folder-id-789abc'
        :return: A Response object containing information about the outcome of the upload operation.
                 This includes details such as HTTP status, headers, and any payload returned by the server.
        """
        item_url = self._get_item_url(
            drive_id=drive_id,
            group_id=group_id,
            site_id=site_id,
            user_id=user_id,
            item_id=parent_item_id,
        )

        # TODO: Consider migrating to different API to allow bigger uploads?

        logger.debug("Uploading: %s (%s)", filename, content_type)
        drive_item: DriveItem = self._request(
            "PUT",
            f"{item_url}:/{filename}:/content",
            data=content,
            extra_headers={"Content-Type": content_type},
        )
        logger.debug("Uploaded: %s to %s", filename, drive_item["id"])
        return drive_item

    def get_delta(
        self,
        delta_link: str | None = None,
        *,
        drive_id: str | None = None,
        group_id: str | None = None,
        site_id: str | None = None,
        user_id: str | None = None,
        item_id: str = "root",
    ) -> DriveItemDelta:
        """
        Retrieve the delta changes for a specific drive item or a delta link provided.

        This function enables tracking changes in a given drive item by using the delta
        API to retrieve the latest updates since the last query. If a delta link is
        provided, it fetches the changes directly from the link. Otherwise, it queries
        the delta changes for the specified item ID in the context of a user, drive,
        group, or site.

        :param delta_link: Delta link to directly fetch the changes. If provided, the
            other parameters are ignored. Can be None.
        :param drive_id: Unique identifier for the drive. Needed for specific drive
            context. Optional and defaults to None.
        :param group_id: Unique identifier for the group. Needed for group-specific
            context. Optional and defaults to None.
        :param site_id: Unique identifier for the site. Needed for site-specific
            context. Optional and defaults to None.
        :param user_id: Unique identifier for the user. Needed for user-specific
            context. Optional and defaults to None.
        :param item_id: Identifier for the specific drive item to track. Defaults to
            "root".
        :return: A `DriveItemDelta` object containing the changes since the last query.
        """
        if delta_link:
            logger.debug("Resolving delta by delta link: %s", delta_link)
            delta = self._request("GET", delta_link, force_default_headers=True)
            logger.debug(
                "Resolving %d delta items for %s", len(delta["value"]), delta_link
            )
            return delta

        item_url = self._get_item_url(
            drive_id=drive_id,
            group_id=group_id,
            site_id=site_id,
            user_id=user_id,
            item_id=item_id,
        )
        logger.debug("Resolving delta by item_url: %s", item_url)
        delta: DriveItemDelta = self._get(f"{item_url}/delta")
        logger.debug("Resolving %d delta items for %s", len(delta["value"]), item_url)
        return delta

    def list_children(
        self,
        *,
        drive_id: str | None = None,
        group_id: str | None = None,
        site_id: str | None = None,
        user_id: str | None = None,
        item_id: str = "root",
    ) -> DriveItemCollection:
        """
        Lists the child items of a specified drive item in a user's Drive, Group Drive, or Site Drive.
        The method determines the appropriate endpoint based on the provided identification parameters
        and retrieves the collection of child items accordingly. If no specific drive identification is
        provided, it defaults to the caller's own Drive ("me").

        :param drive_id: Specifies the unique ID of the drive containing the target item. This parameter
            is optional and mutually exclusive with `group_id`, `site_id`, and `user_id`.
        :param group_id: Specifies the unique ID of the group for accessing the target item's parent drive.
            This parameter is optional and mutually exclusive with `drive_id`, `site_id`, and `user_id`.
        :param site_id: Specifies the unique ID of the site that contains the parent drive for the target item.
            This parameter is optional and mutually exclusive with `drive_id`, `group_id`, and `user_id`.
        :param user_id: Specifies the unique ID of the user who owns the drive containing the target item.
            This parameter is optional and mutually exclusive with `drive_id`, `group_id`, and `site_id`.
        :param item_id: The unique ID of the parent drive item for which children items are to be listed.
            Defaults to `"root"`.
        :return: A `DriveItemCollection` object representing the collection of child items of the specified
            drive item.
        """
        children_url = self._get_children_url(
            drive_id=drive_id,
            group_id=group_id,
            site_id=site_id,
            user_id=user_id,
            item_id=item_id,
        )
        logger.debug("Listing children for: %s", children_url)
        return self._get(children_url)

    def _get_item_url(
        self,
        *,
        drive_id: str | None = None,
        group_id: str | None = None,
        site_id: str | None = None,
        user_id: str | None = None,
        item_id: str = "root",
    ) -> str:
        """
        Generates a URL for accessing a specific item based on provided identifiers. The method
        allows the construction of a URL to target an item within a specified drive, group,
        site, or user context. If no specific identifier is provided, it defaults to the
        current user's "me" drive.

        :param drive_id: Identifier for the drive context. Optional.
        :param group_id: Identifier for the group context. Optional.
        :param site_id: Identifier for the site context. Optional.
        :param user_id: Identifier for the user context. Optional.
        :param item_id: Identifier for the specific item in the drive. Defaults to "root".
        :return: A formatted URL string leading to the specified item.
        """
        if drive_id:
            return f"/drives/{drive_id}/items/{item_id}"
        elif group_id:
            return f"/groups/{group_id}/drive/items/{item_id}"
        elif site_id:
            return f"/sites/{site_id}/drive/items/{item_id}"
        elif user_id:
            return f"/users/{user_id}/drive/items/{item_id}"
        return f"/me/drive/items/{item_id}"

    def _get_children_url(
        self,
        *,
        drive_id: str | None = None,
        group_id: str | None = None,
        site_id: str | None = None,
        user_id: str | None = None,
        item_id: str = "root",
    ) -> str:
        """
        Generates a URL to retrieve the children of a specified item. The function constructs
        the URL based on provided identifiers, such as drive ID, group ID, site ID, user ID,
        and item ID. If not explicitly provided, the function defaults to the root item ID.

        :param drive_id: Optional. The unique identifier of the drive. Default is None.
        :param group_id: Optional. The unique identifier of the group. Default is None.
        :param site_id: Optional. The unique identifier of the site. Default is None.
        :param user_id: Optional. The unique identifier of the user. Default is None.
        :param item_id: The unique identifier of the item whose children are being retrieved.
            Defaults to "root".
        :return: A URL string pointing to the children of the specified item.
        """
        return f"{
            self._get_item_url(
                drive_id=drive_id,
                group_id=group_id,
                site_id=site_id,
                user_id=user_id,
                item_id=item_id,
            )
        }/children"
