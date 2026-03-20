import base64
import io
import zipfile
from collections.abc import Callable, Iterator
from typing import IO, TypedDict

from django.conf import settings

import magic
import py7zr
import requests
import structlog
from elasticsearch.dsl import Document
from zgw_consumers.client import build_client
from zgw_consumers.models import Service

logger = structlog.get_logger(__name__)


class DocumentData(TypedDict):
    document_data: str


type NestedDocumentData = list[DocumentData]


type FileMeta = tuple[IO[bytes], int]


def _iter_zip_content(document_file: io.BytesIO) -> Iterator[FileMeta]:
    with zipfile.ZipFile(file=document_file, mode="r") as zip_file:
        for info in zip_file.infolist():
            with zip_file.open(info.filename) as file:
                yield file, info.file_size


def _iter_7z_content(document_file: io.BytesIO) -> Iterator[FileMeta]:
    with py7zr.SevenZipFile(document_file, mode="r") as zip_file:
        if not (zip_file_dict := zip_file.readall()):
            return
        filesizes: dict[str, int] = {
            file_info.filename: file_info.uncompressed for file_info in zip_file.list()
        }
        for name, file in zip_file_dict.items():
            yield file, filesizes[name]


def _extract_documents(
    document_file: io.BytesIO, iter_archive: Callable[[io.BytesIO], Iterator[FileMeta]]
) -> NestedDocumentData:
    file_list: NestedDocumentData = []
    total_size: int = 0

    for file, size_in_bytes in iter_archive(document_file):
        document_mime = magic.from_buffer(file.read(2048), mime=True)
        # NOTE: we deliberately do not recurse into nested archives, see

        if document_mime not in settings.SEARCH_INDEXABLE_FILE_TYPES:
            logger.debug("file_skipped", extra={"mime_type": document_mime})
            continue

        # update the total size based on the non-base64 encoded file size - we don't
        # assign it yet because there may be smaller files that we can still stuff into
        # the document data
        new_total_size = total_size + size_in_bytes
        if new_total_size > settings.SEARCH_INDEX["MAX_INDEX_FILE_SIZE"]:
            logger.debug(
                "file_skipped", extra={"reason": "exceeding_max_index_file_size"}
            )
            continue

        # okay, we have headroom, prepare the file and next loop iteration
        total_size = new_total_size
        # now read the full file - there's still a risk if going OOM here if the
        # compression ratio is very high
        file.seek(0)
        file_contents = file.read()
        document_data = base64.b64encode(file_contents).decode("ascii")
        file_list.append({"document_data": document_data})

        # once our limit is reached, we can stop processing the archives entirely
        if total_size >= settings.SEARCH_INDEX["MAX_INDEX_FILE_SIZE"]:
            break

    return file_list


def _download_document(document_url: str) -> NestedDocumentData | None:
    # TODO test here with the same document zgw_group service
    if (service := Service.get_service(document_url)) is None:
        logger.exception("service_not_found")
        return None

    with build_client(service) as client:
        try:
            response = client.get(
                url=document_url,
                headers={  # TODO: improve the way we set the headers
                    "Audit-User-Representation": "Open DMS (system)",
                    "Audit-User-ID": "Open DMS",
                    "Audit-Remarks": "download document for indexing.",
                },
            )
            response.raise_for_status()
        except requests.RequestException:
            logger.exception("Could not download the document at %s.", document_url)
            return None
        # TODO check Timeout

    _content_type = response.headers.get("Content-Type")

    with io.BytesIO(initial_bytes=response.content) as document_file:
        document_mime = magic.from_buffer(document_file.read(2048), mime=True)
        document_file.seek(0)

        # Arch Linux shared mimetypes doesn't properly detect application/zip :(
        if (
            document_mime == "application/octet-stream"
            and _content_type == "application/zip"
        ):  # pragma: no cover
            document_mime = "application/zip"

        match document_mime:
            case "application/zip":
                return list(_extract_documents(document_file, _iter_zip_content))
            # Don't need extra introspection like open-forms (gh #4658)
            # Because we only rely on magic type and not the received content_type
            case "application/x-7z-compressed":
                return list(_extract_documents(document_file, _iter_7z_content))
            case _:
                return [
                    {
                        "document_data": base64.b64encode(response.content).decode(
                            "ascii"
                        )
                    }
                ]


def get_subclasses(cls: type):
    for subclass in cls.__subclasses__():
        yield from get_subclasses(subclass)
        yield subclass


def get_index_document_types() -> Iterator[type[Document]]:
    yield from get_subclasses(Document)
