from __future__ import annotations

from typing import Any, Callable, Dict, Optional
from urllib.parse import quote

from ._resource import body as _body, query as _query

RequestFn = Callable[..., Any]


class Segments:
    """The ``segments`` resource. Access via ``mailtea.segments``.

    Audience segments are scoped to a publication — pass ``publication_id``.
    Every method accepts the payload as a wire-format dict, as keyword
    arguments, or both. To clear a nullable filter on update, pass ``None``
    (e.g. ``status_filter=None``); omit the key to leave it unchanged.

    Filters are ``status_filter``, ``query_filter`` and ``inactive_days``.
    ``inactive_days`` (an integer, 1 to 3650) selects contacts with no open
    or click in the last N days; a contact who never engaged counts as
    inactive, so it finds the silent cohort for a sunset or re-engagement
    send, not engaged readers. Engagement tracking is not backfilled, so
    contacts with no recorded engagement count as inactive, including some
    who opened or clicked before tracking began. Any filter makes
    the segment a filter segment, and a segment with contacts added to it
    cannot take one. Every segment reply carries ``inactive_days`` (``None``
    when unset).
    """

    def __init__(self, request: RequestFn) -> None:
        self._request = request

    def create(self, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        return self._request("POST", "/v1/segments", _body(params, kwargs))

    def list(self, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        return self._request("GET", "/v1/segments" + _query(_body(params, kwargs)))

    def get(self, id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        return self._request(
            "GET", "/v1/segments/" + quote(str(id), safe="") + _query(_body(params, kwargs))
        )

    def update(self, id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        merged = _body(params, kwargs)
        return self._request(
            "PATCH",
            "/v1/segments/"
            + quote(str(id), safe="")
            + _query({"publication_id": merged.get("publication_id")}),
            merged,
        )

    def delete(self, id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Delete a segment. A segment that a draft, scheduled or sending post
        targets cannot be deleted: the request fails with a 409
        :class:`~mailtea.errors.MailteaError` (``code`` ``segment_in_use``) and
        nothing is deleted. Point those posts at another segment, or set their
        ``segment_id`` to ``None``, first."""
        return self._request(
            "DELETE", "/v1/segments/" + quote(str(id), safe="") + _query(_body(params, kwargs))
        )
