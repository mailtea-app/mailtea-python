from __future__ import annotations

from typing import Any, Callable, Dict, Optional
from urllib.parse import quote

from ._resource import body as _body, query as _query

RequestFn = Callable[..., Any]


class Templates:
    """The ``templates`` resource (reusable server-side email templates). Access
    via ``mailtea.templates``.

    Templates are scoped to a publication — pass ``publication_id`` (except
    :meth:`render`, which just renders a spec). Create one from raw ``html`` or a
    json-render ``spec``, then :meth:`publish` it before seeding posts/emails
    from it. Every method accepts the payload as a wire-format dict, as keyword
    arguments, or both (use ``from_=`` as the keyword form of ``"from"``).
    """

    def __init__(self, request: RequestFn) -> None:
        self._request = request

    def render(self, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Render a json-render ``spec`` (with optional ``variables``) to HTML
        without creating a template. Returns ``{"html": ..., "text": ...}``."""
        return self._request("POST", "/v1/templates/render", _body(params, kwargs))

    def create(self, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Create a template from ``html`` OR a ``spec`` (one is required). Takes
        ``publication_id`` and ``name``, plus optional ``description``, ``text``,
        ``subject``, ``from``, ``reply_to``, and ``variables``."""
        return self._request("POST", "/v1/templates", _body(params, kwargs))

    def list(self, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """List templates (cursor-paginated). Filters: ``publication_id``
        (required), ``limit``, ``after`` (cursor from a previous ``next_cursor``)."""
        return self._request("GET", "/v1/templates" + _query(_body(params, kwargs)))

    def get(self, id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        return self._request(
            "GET", "/v1/templates/" + quote(str(id), safe="") + _query(_body(params, kwargs))
        )

    def update(self, id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Update a template's ``name``, ``html``/``spec``, ``description``,
        ``text``, ``subject``, ``from``, ``reply_to``, or ``variables``.
        ``publication_id`` is required (sent as a query parameter)."""
        merged = _body(params, kwargs)
        return self._request(
            "PATCH",
            "/v1/templates/"
            + quote(str(id), safe="")
            + _query({"publication_id": merged.get("publication_id")}),
            merged,
        )

    def publish(self, id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Publish a template so it can seed posts/emails. Requires ``publication_id``."""
        return self._request(
            "POST",
            "/v1/templates/" + quote(str(id), safe="") + "/publish" + _query(_body(params, kwargs)),
        )

    def duplicate(self, id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Duplicate a template into a new draft. Requires ``publication_id``."""
        return self._request(
            "POST",
            "/v1/templates/" + quote(str(id), safe="") + "/duplicate" + _query(_body(params, kwargs)),
        )

    def delete(self, id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        return self._request(
            "DELETE", "/v1/templates/" + quote(str(id), safe="") + _query(_body(params, kwargs))
        )
