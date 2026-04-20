import io
import mimetypes
import zipfile

import magic
from requests import Response


def guess_extension_by_response(response: Response) -> str:
    """
    TODO: Add more advanced detection logic
    """
    return guess_extension_by_content(response.content)


def guess_extension_by_content(content: bytes) -> str:
    """
    Determines the file extension based on its content.

    This function attempts to detect the file type by analyzing the provided
    byte content. It uses the MIME type inferred from the content and refines
    the result for specific cases like zipped office documents or OpenDocument
    formats based on further inspection.

    Args:
        content (bytes): The file content to be analyzed.

    Returns:
        str: The guessed file extension (e.g., ".docx", ".xlsx", ".bin").
    """
    mime_type = magic.from_buffer(content, mime=True)
    guessed_extension = mimetypes.guess_extension(mime_type) or ".bin"

    match guessed_extension:
        case ".zip":
            # (Most) Office documents are technically .zip files, attempt to find the actual type.
            try:
                with zipfile.ZipFile(io.BytesIO(content)) as z:
                    names = set(z.namelist())

                    if "[Content_Types].xml" in names:
                        if any(n.startswith("word/") for n in names):
                            return ".docx"
                        if any(n.startswith("xl/") for n in names):
                            return ".xlsx"
                        if any(n.startswith("ppt/") for n in names):
                            return ".pptx"

                    if "mimetype" in names:
                        mt = z.read("mimetype").decode(errors="ignore")
                        if "opendocument.text" in mt:
                            return ".odt"
                        if "opendocument.spreadsheet" in mt:
                            return ".ods"

            # Probably not an office document, pass to return guessed_extension.
            except Exception:
                pass

    return guessed_extension
