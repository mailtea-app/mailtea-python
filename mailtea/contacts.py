from __future__ import annotations

from typing import Any, Callable, Dict, Optional
from urllib.parse import quote

from ._resource import body as _body, query as _query

RequestFn = Callable[..., Any]


class Contacts:
    """The ``contacts`` resource. Access via ``mailtea.contacts``.

    Audience resources are scoped to a publication — pass ``publication_id``.
    Every method accepts the payload as a wire-format dict, as keyword
    arguments, or both.
    """

    def __init__(self, request: RequestFn) -> None:
        self._request = request

    def create(self, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Create a contact — or update it if the email already exists in the
        publication (the endpoint upserts). :meth:`upsert` is the same call."""
        return self._request("POST", "/v1/contacts", _body(params, kwargs))

    def upsert(self, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Create the contact or update it in place — alias of :meth:`create`,
        named for what ``POST /v1/contacts`` actually does."""
        return self.create(params, **kwargs)

    def list(self, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """List contacts (cursor-paginated). Filters: ``publication_id``
        (required), ``status`` (``active``/``unsubscribed``/``suppressed``),
        ``search`` (matches the email address), ``limit``, ``after`` (cursor
        from a previous ``next_cursor``)."""
        return self._request("GET", "/v1/contacts" + _query(_body(params, kwargs)))

    def get(self, id_or_email: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        return self._request(
            "GET",
            "/v1/contacts/" + quote(str(id_or_email), safe="") + _query(_body(params, kwargs)),
        )

    def update(self, id_or_email: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        merged = _body(params, kwargs)
        return self._request(
            "PATCH",
            "/v1/contacts/"
            + quote(str(id_or_email), safe="")
            + _query({"publication_id": merged.get("publication_id")}),
            merged,
        )

    def delete(self, id_or_email: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        return self._request(
            "DELETE",
            "/v1/contacts/" + quote(str(id_or_email), safe="") + _query(_body(params, kwargs)),
        )

    def set_property_values(
        self, id_or_email: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> Dict[str, Any]:
        """Set this contact's property values — the data behind
        ``{{contact.<key>}}`` merge tags.

        Creating a property with ``mailtea.contact_properties.create`` only
        defines the field; this is what puts a value on a contact.

        Each entry in ``values`` identifies one property by ``key`` OR
        ``property_id`` — exactly one, never both. ``key`` is usually what you
        have, since it is the name written in the template. An empty ``value``
        CLEARS the property, which makes its ``fallback_value`` apply again on
        the next send.

        >>> mailtea.contacts.set_property_values(
        ...     "con_abc123",
        ...     publication_id="pub_abc123",
        ...     values=[{"key": "first_name", "value": "Ada"}],
        ... )
        """
        merged = _body(params, kwargs)
        return self._request(
            "PUT",
            "/v1/contacts/" + quote(str(id_or_email), safe="") + "/properties",
            merged,
        )

    def list_property_values(
        self, id_or_email: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> Dict[str, Any]:
        """Read this contact's property values. Requires ``publication_id``."""
        return self._request(
            "GET",
            "/v1/contacts/"
            + quote(str(id_or_email), safe="")
            + "/properties"
            + _query(_body(params, kwargs)),
        )
