from __future__ import annotations

from typing import Any, Callable, Dict, Optional
from urllib.parse import quote

from ._resource import body as _body, query as _query

RequestFn = Callable[..., Any]


class Senders:
    """The ``senders`` resource (named From identities). Access via ``mailtea.senders``.

    Senders are scoped to a publication — pass ``publication_id``. ``create``
    takes ``name`` and ``email`` (the address must live on a verified,
    DKIM-verified email domain), plus optional ``reply_to`` and ``is_default``.
    The ``email`` is immutable, so :meth:`update` only changes ``name``,
    ``reply_to``, and ``is_default``. Every method accepts the payload as a
    wire-format dict, as keyword arguments, or both.
    """

    def __init__(self, request: RequestFn) -> None:
        self._request = request

    def create(self, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        return self._request("POST", "/v1/senders", _body(params, kwargs))

    def list(self, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """List senders (cursor-paginated). Filters: ``publication_id`` (required),
        ``limit``, ``after`` (cursor from a previous ``next_cursor``)."""
        return self._request("GET", "/v1/senders" + _query(_body(params, kwargs)))

    def get(self, id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        return self._request(
            "GET", "/v1/senders/" + quote(str(id), safe="") + _query(_body(params, kwargs))
        )

    def update(self, id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Update a sender's ``name``, ``reply_to``, or ``is_default`` (the
        ``email`` is immutable). ``publication_id`` is required in the body."""
        return self._request(
            "PATCH", "/v1/senders/" + quote(str(id), safe=""), _body(params, kwargs)
        )

    def delete(self, id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        return self._request(
            "DELETE", "/v1/senders/" + quote(str(id), safe="") + _query(_body(params, kwargs))
        )
