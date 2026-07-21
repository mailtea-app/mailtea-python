from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from ._resource import body as _body, query as _query

RequestFn = Callable[..., Any]


class Suppressions:
    """The ``suppressions`` resource (the org-wide do-not-send list). Access via
    ``mailtea.suppressions``.

    Suppressions are team-scoped — there is no ``publication_id``. Every method
    accepts the payload as a wire-format dict, as keyword arguments, or both.
    """

    def __init__(self, request: RequestFn) -> None:
        self._request = request

    def list(self, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """List suppression entries (cursor-paginated). Optional filters:
        ``reason``, ``q`` (email search), ``created_after``, ``created_before``,
        ``limit``, ``starting_after`` (cursor from a previous ``next_cursor``)."""
        return self._request("GET", "/v1/suppressions" + _query(_body(params, kwargs)))

    def add(self, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Add addresses to the suppression list. Takes ``emails`` (a list, up to
        1000) and an optional ``reason``. Returns ``{"added": ...}``."""
        return self._request("POST", "/v1/suppressions", _body(params, kwargs))

    def remove(self, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Remove addresses from the suppression list. Takes ``emails`` (a list).
        Returns ``{"removed": ...}``."""
        return self._request("DELETE", "/v1/suppressions", _body(params, kwargs))

    def export(self) -> str:
        """Export the whole suppression list as CSV. Returns the raw ``text/csv``
        body (``email,reason,source,created_at`` with a header row), not JSON."""
        return self._request("GET", "/v1/suppressions/export", raw=True)
