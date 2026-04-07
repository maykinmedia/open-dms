from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import TypedDict


class Application(TypedDict):
    id: str
    displayName: str


class User(TypedDict):
    email: str
    id: str
    displayName: str


class CreatedBy(TypedDict, total=False):
    application: Application | None
    user: User


class ParentReference(TypedDict):
    driveType: str
    driveId: str
    id: str
    name: str
    path: str
    siteId: str


class FileSystemInfo(TypedDict):
    createdDateTime: str
    lastModifiedDateTime: str


class Folder(TypedDict, total=False):
    childCount: int


class FileHashes(TypedDict):
    quickXorHash: str


class FileInfo(TypedDict):
    # TODO check if you can add also the name here o the document url
    fileExtension: str
    hashes: FileHashes
    mimeType: str


class LinkType(StrEnum):
    VIEW = "view"
    EDIT = "edit"
    EMBED = "embed"


class LinkScope(StrEnum):
    ANONYMOUS = "anonymous"
    ORGANIZATION = "organization"
    USERS = "users"


@dataclass
class ShareLink:
    id: str
    web_url: str
    type: LinkType
    scope: LinkScope
    expiration: datetime | None = None
    has_password: bool = False

    @classmethod
    def from_response(cls, data: dict) -> "ShareLink":
        link = data["link"]
        expiry_raw = data.get("expirationDateTime")
        return cls(
            id=data["id"],
            web_url=link["webUrl"],
            type=LinkType(link["type"]),
            scope=LinkScope(link["scope"]),
            expiration=datetime.fromisoformat(expiry_raw) if expiry_raw else None,
            has_password=data.get("hasPassword", False),
        )


class SpecialFolder(TypedDict):
    name: str


DriveItem = TypedDict(
    "DriveItem",
    {
        "createdBy": CreatedBy,
        "createdDateTime": str,
        "eTag": str,
        "id": str,
        "lastModifiedBy": CreatedBy,
        "lastModifiedDateTime": str,
        "name": str,
        "parentReference": ParentReference,
        "webUrl": str,
        "cTag": str,
        "fileSystemInfo": FileSystemInfo,
        "folder": Folder | dict,  # {} for create
        "file": FileInfo | dict,  # {} for create
        "size": int,
        "specialFolder": SpecialFolder,
        "@microsoft.graph.conflictBehavior": str,
    },
    total=False,
)

# Special chars
DriveItemCollection = TypedDict(
    "DriveItemCollection", {"@odata.context": str, "value": list[DriveItem]}
)

# Special chars
DriveItemDelta = TypedDict(
    "DriveItemDelta", {"@odata.deltaLink": str | None, "value": list[DriveItem]}
)
