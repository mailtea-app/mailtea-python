from __future__ import annotations

from typing import Any, Callable, Dict
from urllib.parse import quote

RequestFn = Callable[..., Any]


class ApiKeys:
    """The ``api_keys`` resource. Access via ``mailtea.api_keys``.

    Requires a token with ``settings:write``. A key can never be granted scopes
    the calling token does not already hold.
    """

    def __init__(self, request: RequestFn) -> None:
        self._request = request

    def create(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create an API key. The ``token`` is returned ONCE — store it securely.

        ``params`` takes ``name``, optional ``permission`` (``"full_access"`` or
        ``"sending_access"``), and optional ``domain_id``.
        """
        return self._request("POST", "/v1/api-keys", params)

    def list(self) -> Dict[str, Any]:
        """List API keys (token values are never returned)."""
        return self._request("GET", "/v1/api-keys")

    def revoke(self, id: str) -> Any:
        """Revoke (delete) an API key by id."""
        return self._request("DELETE", "/v1/api-keys/" + quote(str(id), safe=""))
