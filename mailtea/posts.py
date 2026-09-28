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
        server template with ``template_id`` + ``variables``, using the
        template's PUBLISHED version and not any unpublished edits saved since,
        or pass inline ``html``. The ``variables`` you pass are filled in, in
        both the ``{{key}}`` and Visual Email Designer ``{key}`` forms, and
        HTML-escaped (use ``{{{key}}}`` in the template for raw HTML).
        Everything else is left for the broadcast to fill per recipient: a
        declared variable you do not pass keeps its ``fallback_value`` for
        recipients with no value, and undeclared tokens like
        ``{{contact.first_name}}`` stay as they are. The post keeps the
        template's published page style. ``kind`` selects
        the post type (``"newsletter"`` or ``"broadcast"``). Set
        ``send=True`` to deliver right after creating (or with
        ``scheduled_at`` to schedule); that requires the ``issues:send``
        scope.

        ``subject`` is the subject line subscribers see. ``name`` is only the
        post's internal name in Mailtea Studio and never becomes the subject.
        ``from`` (keyword ``from_=``) must be on one of the publication's
        verified sending domains, or the request is refused with a 422; a From
        on the built-in ``*.mailtea.email`` address is kept for test emails, but
        the post itself sends from the publication's default sender.
        ``reply_to`` must be a valid email address. Both are kept on the post.

        Returns ``{"id": ...}``.
        """
        return self._request("POST", "/v1/posts", _body(params, kwargs))

    def list(self, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """List posts (most recent first, offset-paginated). Takes ``publication_id``
        (required) plus optional ``limit``, ``offset``, ``status``, and ``kind``
        (``"newsletter"`` or ``"broadcast"``). Returns ``{"data", "total"}``."""
        return self._request("GET", "/v1/posts" + _query(_body(params, kwargs)))

    def get(self, id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Retrieve a post by id. Includes ``name`` (the internal name, equal to
        ``subject`` when not set), ``from`` and ``reply_to`` (``None`` when the
        named sender or the publication default decides)."""
        return self._request(
            "GET", "/v1/posts/" + quote(str(id), safe="") + _query(_body(params, kwargs))
        )

    def update(self, id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Update a draft post (sent posts are immutable). Accepts ``subject``,
        ``html``, ``text``, ``from`` (keyword ``from_=``), ``reply_to``, and
        ``name``. Only the fields you pass change; ``""`` clears ``name``,
        ``from`` or ``reply_to``. Renaming never changes the subject, and
        ``from`` is gated like ``create``.

        Pass ``base_updated_at`` (the post's ``updated_at`` as you last read
        it, from :meth:`get`) to require the post still be unchanged since;
        otherwise the write fails with :class:`~mailtea.errors.MailteaError`
        (``code`` ``stale_write``; the response body also carries
        ``current_updated_at``) and nothing is saved. Re-read, re-apply your
        change, and retry. Omit it for an unconditional write. The reply now
        also carries ``updated_at``."""
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
