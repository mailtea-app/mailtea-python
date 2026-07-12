from __future__ import annotations

from typing import Any, Optional


class MailteaError(Exception):
    """Raised when the Mailtea API returns an error or the client is misconfigured.

    Attributes:
        status: HTTP status code (0 for client-side errors).
        code: machine-readable code for client-side errors (e.g. ``missing_api_key``).
        details: validation issue list returned by the API, if any.
        request_id: the API's ``x-request-id`` for support/debugging.
    """

    def __init__(
        self,
        message: str,
        *,
        status: int = 0,
        code: Optional[str] = None,
        details: Any = None,
        request_id: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status = status
        self.code = code
        self.details = details
        self.request_id = request_id
