from __future__ import annotations

from typing import Any, Callable, Dict, Optional
from urllib.parse import quote

from ._resource import body as _body, query as _query

RequestFn = Callable[..., Any]


class ContactProperties:
    """The ``contact_properties`` resource (custom contact fields). Access via
    ``mailtea.contact_properties``.

    Definitions are team-scoped — there is no ``publication_id``. ``create``
    takes ``key`` and ``type`` (``"string"`` or ``"number"``). Every method
    accepts the payload as a wire-format dict, as keyword arguments, or both.
    """

    def __init__(self, request: RequestFn) -> None:
        self._request = request

    def create(self, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        return self._request("POST", "/v1/contact-properties", _body(params, kwargs))

    def list(self, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        return self._request("GET", "/v1/contact-properties" + _query(_body(params, kwargs)))

    def update(self, id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        return self._request(
            "PATCH", "/v1/contact-properties/" + quote(str(id), safe=""), _body(params, kwargs)
        )

    def delete(self, id: str) -> Dict[str, Any]:
        return self._request(
            "DELETE", "/v1/contact-properties/" + quote(str(id), safe="")
        )
