from __future__ import annotations

from typing import Any, Callable, Dict, Optional
from urllib.parse import quote, urlencode

RequestFn = Callable[..., Any]


class Segments:
    """The ``segments`` resource. Access via ``mailtea.segments``.

    Audience segments are scoped to a publication — pass ``publication_id``.
    Payloads are plain dicts matching the REST wire format. To clear a nullable
    filter on update, pass ``None`` (e.g. ``{"status_filter": None}``); omit the
    key to leave it unchanged.
    """

    def __init__(self, request: RequestFn) -> None:
        self._request = request

    def create(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/v1/segments", params)

    def list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("GET", "/v1/segments" + _query(params))

    def get(self, id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        return self._request(
            "GET", "/v1/segments/" + quote(str(id), safe="") + _query(params)
        )

    def update(self, id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        return self._request(
            "PATCH",
            "/v1/segments/"
            + quote(str(id), safe="")
            + _query({"publication_id": params.get("publication_id")}),
            params,
        )

    def delete(self, id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        return self._request(
            "DELETE", "/v1/segments/" + quote(str(id), safe="") + _query(params)
        )


def _query(params: Optional[Dict[str, Any]]) -> str:
    if not params:
        return ""
    clean = {key: value for key, value in params.items() if value is not None}
    return ("?" + urlencode(clean)) if clean else ""
