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
