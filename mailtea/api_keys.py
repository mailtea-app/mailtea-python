from __future__ import annotations

from typing import Any, Callable, Dict, Optional
from urllib.parse import quote

from ._resource import body as _body

RequestFn = Callable[..., Any]


class ApiKeys:
    """The ``api_keys`` resource. Access via ``mailtea.api_keys``.

    ``create``, ``list`` and ``revoke`` require a token with ``settings:write``.
    A key can never be granted scopes the calling token does not already hold.
    ``current`` needs no scope.
    """

    def __init__(self, request: RequestFn) -> None:
        self._request = request

    def create(self, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Create an API key. The ``token`` is returned ONCE — store it securely.

        Takes ``name``, optional ``permission`` (``"full_access"`` or
        ``"sending_access"``), optional ``domain_id``, and optional ``mode``.
        Accepts a wire-format dict, keyword arguments, or both.

        ``mode`` is ``"live"`` (the default) or ``"test"``. A test key is prefixed
        ``mt_test_``: its sends are validated, recorded and emit webhooks but are
        never delivered, and it reads only test mail. It is NOT a data sandbox --
        it reads and writes your real contacts, templates, senders and webhooks.
        Only delivery is simulated. The response carries the ``mode`` the key was
        minted in.
        """
        return self._request("POST", "/v1/api-keys", _body(params, kwargs))

    def list(self) -> Dict[str, Any]:
        """List API keys (token values are never returned)."""
        return self._request("GET", "/v1/api-keys")

    def current(self) -> Dict[str, Any]:
        """Describe the key making the request: ``team``, ``publication`` (with
        its ``receiving_domain``, or None for a team-wide key), ``scopes``,
        ``mode`` and ``plan`` (``daily_limit`` and ``monthly_limit`` are hard
        limits, None means none; ``ramp`` is the new-team daily limit while it
        lasts). Any key may call it."""
        return self._request("GET", "/v1/api-keys/current")

    def revoke(self, id: str) -> Any:
        """Revoke (delete) an API key by id."""
        return self._request("DELETE", "/v1/api-keys/" + quote(str(id), safe=""))
