from __future__ import annotations

from typing import Any, Callable, Dict, Optional
from urllib.parse import quote, urlencode

RequestFn = Callable[..., Any]


class Tags:
    """The ``tags`` resource (tag definitions). Access via ``mailtea.tags``.

    Tags are scoped to a publication — pass ``publication_id``. ``create``
    requires ``default_subscription`` (``"opt_in"`` or ``"opt_out"``). This
    manages tag definitions only; assigning tags to contacts is not yet exposed.
    """

    def __init__(self, request: RequestFn) -> None:
        self._request = request

    def create(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/v1/tags", params)

    def list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("GET", "/v1/tags" + _query(params))

    def get(self, id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        return self._request(
            "GET", "/v1/tags/" + quote(str(id), safe="") + _query(params)
        )

    def update(self, id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        return self._request(
            "PATCH",
            "/v1/tags/"
            + quote(str(id), safe="")
            + _query({"publication_id": params.get("publication_id")}),
            params,
        )

    def delete(self, id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        return self._request(
            "DELETE", "/v1/tags/" + quote(str(id), safe="") + _query(params)
        )


def _query(params: Optional[Dict[str, Any]]) -> str:
    if not params:
        return ""
    clean = {key: value for key, value in params.items() if value is not None}
    return ("?" + urlencode(clean)) if clean else ""
