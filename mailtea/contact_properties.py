from __future__ import annotations

from typing import Any, Callable, Dict, Optional
from urllib.parse import quote, urlencode

RequestFn = Callable[..., Any]


class ContactProperties:
    """The ``contact_properties`` resource (custom contact fields). Access via
    ``mailtea.contact_properties``.

    Definitions are team-scoped — there is no ``publication_id``. ``create``
    takes ``key`` and ``type`` (``"string"`` or ``"number"``).
    """

    def __init__(self, request: RequestFn) -> None:
        self._request = request

    def create(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/v1/contact-properties", params)

    def list(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self._request("GET", "/v1/contact-properties" + _query(params))

    def update(self, id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        return self._request(
            "PATCH", "/v1/contact-properties/" + quote(str(id), safe=""), params
        )

    def delete(self, id: str) -> Dict[str, Any]:
        return self._request(
            "DELETE", "/v1/contact-properties/" + quote(str(id), safe="")
        )


def _query(params: Optional[Dict[str, Any]]) -> str:
    if not params:
        return ""
    clean = {key: value for key, value in params.items() if value is not None}
    return ("?" + urlencode(clean)) if clean else ""
