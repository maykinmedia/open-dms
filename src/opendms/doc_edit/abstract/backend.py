from typing import Protocol

from django.http import HttpResponseRedirect

from rest_framework.request import Request
from rest_framework.response import Response


class DocumentEditBackend(Protocol):
    def authenticate(
        self, request: Request, redirect_url: str | None = None
    ) -> HttpResponseRedirect:
        """
        Begin an authentication process.

        :param request: Request object
        :param redirect_url: A URL to return to after authentication completes.
        :return: A response that continues or initiates authentication.
        """
        pass  # noqa

    def authenticated_callback(self, request: Request) -> Response | None:
        """
        Handle a callback related to authentication.

        :param request: Request object
        :return: A response indicating the result of the callback handling.
        :raises PermissionError: If the login is not successful.
        """
        pass  # noqa

    def open(
        self, request: Request, file_path: str, file_name: str, file_ext: str
    ) -> HttpResponseRedirect:
        """
        Start a process to access or edit a file.

        :param request: Request object
        :param file_path: Full path of the target file.
        :param file_name: File name.
        :param file_ext: File extension.
        :return: A response that continues the file access/edit flow.
        :raises FileNotFoundError: If the file is not found.
        :raises BlockingIOError: If the file cannot be accessed at this time.
        """
        pass  # noqa

    def updated_callback(self, request: Request) -> Response:
        """
        Handle a callback indicating that a file or resource has changed.

        :param request: Request object
        :return: A response acknowledging or processing the update.
        """
        pass  # noqa
