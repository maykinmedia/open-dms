from typing import Protocol

from rest_framework.request import Request
from rest_framework.response import Response


class DocumentEditBackend(Protocol):
    def authenticate(self, redirect_url: str | None = None) -> Response:
        """
        Begin an authentication process.

        :param redirect_url: A URL to return to after authentication completes.
        :return: A response that continues or initiates authentication.
        """
        pass  # noqa

    def authenticated_callback(self, request: Request) -> Response | None:
        """
        Handle a callback related to authentication.

        :param request: The incoming request containing callback data.
        :return: A response indicating the result of the callback handling.
        :raises PermissionError: If the login is not successful.
        """
        pass  # noqa

    def open(self, file_path: str) -> Response:
        """
        Start a process to access or edit a file.

        :param file_path: Identifier or path of the target file.
        :return: A response that continues the file access/edit flow.
        :raises FileNotFoundError: If the file is not found.
        :raises BlockingIOError: If the file cannot be accessed at this time.
        """
        pass  # noqa

    def updated_callback(self, request: Request) -> Response:
        """
        Handle a callback indicating that a file or resource has changed.

        :param request: The incoming request containing update information.
        :return: A response acknowledging or processing the update.
        """
        pass  # noqa
