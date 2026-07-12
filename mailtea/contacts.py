from __future__ import annotations

from typing import Any, Callable, Dict, Optional
from urllib.parse import quote, urlencode

RequestFn = Callable[..., Any]


class Contacts:
    """The ``contacts`` resource. Access via ``mailtea.contacts``.

    Audience resources are scoped to a publication — pass ``publication_id``.
    """

    def __init__(self, request: RequestFn) -> None:
        self._request = request

    def create(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/v1/contacts", params)

    def list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("GET", "/v1/contacts" + _query(params))

    def get(self, id_or_email: str, params: Dict[str, Any]) -> Dict[str, Any]:
        return self._request(
            "GET", "/v1/contacts/" + quote(str(id_or_email), safe="") + _query(params)
        )

    def update(self, id_or_email: str, params: Dict[str, Any]) -> Dict[str, Any]:
        return self._request(
            "PATCH",
            "/v1/contacts/"
            + quote(str(id_or_email), safe="")
            + _query({"publication_id": params.get("publication_id")}),
            params,
        )

    def delete(self, id_or_email: str, params: Dict[str, Any]) -> Dict[str, Any]:
        return self._request(
            "DELETE", "/v1/contacts/" + quote(str(id_or_email), safe="") + _query(params)
        )


def _query(params: Optional[Dict[str, Any]]) -> str:
    if not params:
        return ""
    clean = {key: value for key, value in params.items() if value is not None}
    return ("?" + urlencode(clean)) if clean else ""
