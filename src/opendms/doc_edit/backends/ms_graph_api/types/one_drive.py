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
    fileExtension: str
    hashes: FileHashes
    mimeType: str


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
