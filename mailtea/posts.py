from __future__ import annotations

from typing import Any, Callable, Dict, Optional
from urllib.parse import quote

from ._resource import body as _body, query as _query

RequestFn = Callable[..., Any]


class Posts:
    """The ``posts`` resource (newsletter posts/issues). Access via ``mailtea.posts``.

    Every method accepts the payload as a wire-format dict, as keyword
    arguments, or both (snake_case keys like ``reply_to``; use ``from_=`` as
    the keyword form of ``"from"``).
    """

    def __init__(self, request: RequestFn) -> None:
        self._request = request

    def create(self, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Create a newsletter post (draft by default). Seed it from a published
        server template with ``template_id`` + ``variables``, or pass inline
        ``html``. ``kind`` selects the post type (``"newsletter"`` or
        ``"broadcast"``). Set ``send=True`` to deliver right after creating (or
        with ``scheduled_at`` to schedule) — that requires the ``issues:send`` scope.

        Returns ``{"id": ...}``.
        """
        return self._request("POST", "/v1/posts", _body(params, kwargs))

    def list(self, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """List posts (most recent first, offset-paginated). Takes ``publication_id``
        (required) plus optional ``limit``, ``offset``, ``status``, and ``kind``
        (``"newsletter"`` or ``"broadcast"``). Returns ``{"data", "total"}``."""
        return self._request("GET", "/v1/posts" + _query(_body(params, kwargs)))

    def get(self, id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Retrieve a post by id."""
        return self._request(
            "GET", "/v1/posts/" + quote(str(id), safe="") + _query(_body(params, kwargs))
        )

    def update(self, id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Update a draft post (sent posts are immutable). Accepts ``subject``,
        ``html``, ``text``, ``from``, ``reply_to``, and ``name``."""
        return self._request(
            "PATCH", "/v1/posts/" + quote(str(id), safe=""), _body(params, kwargs)
        )

    def delete(self, id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Delete a draft post (sent posts cannot be deleted)."""
        return self._request(
            "DELETE", "/v1/posts/" + quote(str(id), safe="") + _query(_body(params, kwargs))
        )

    def send(self, id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Send a draft post to the publication's audience — immediately, or at
        ``scheduled_at`` (ISO 8601) if given. Requires the ``issues:send`` scope.
        """
        merged = _body(params, kwargs)
        return self._request(
            "POST", "/v1/posts/" + quote(str(id), safe="") + "/send", merged or None
        )

    def send_test(self, id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Send a TEST copy of a post to specific recipients to check it before
        subscribers see it. Renders the post exactly as a subscriber would receive
        it and delivers a one-shot ``[TEST]`` email — it does NOT send to the
        audience.

        Takes ``recipients`` (up to 10), ``from`` (must use a verified domain),
        and optional ``reply_to``. Returns ``{"sent_to": [...], "failed_to": [...]}``.
        """
        return self._request(
            "POST", "/v1/posts/" + quote(str(id), safe="") + "/test", _body(params, kwargs)
        )
