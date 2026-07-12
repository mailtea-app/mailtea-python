from __future__ import annotations

from typing import Any, Callable, Dict, Optional
from urllib.parse import quote, urlencode

RequestFn = Callable[..., Any]

_BASE = "/v1/webhooks/endpoints"


class Webhooks:
    """The ``webhooks`` resource (outbound event subscriptions). Access via
    ``mailtea.webhooks``.

    Scoped to a publication — pass ``publication_id``. ``create`` returns the
    ``signing_secret`` once; store it to verify payload signatures.
    """

    def __init__(self, request: RequestFn) -> None:
        self._request = request

    def create(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", _BASE, params)

    def list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("GET", _BASE + _query(params))

    def get(self, id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        return self._request(
            "GET", _BASE + "/" + quote(str(id), safe="") + _query(params)
        )

    def update(self, id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        return self._request(
            "PATCH",
            _BASE
            + "/"
            + quote(str(id), safe="")
            + _query({"publication_id": params.get("publication_id")}),
            params,
        )

    def delete(self, id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        return self._request(
            "DELETE", _BASE + "/" + quote(str(id), safe="") + _query(params)
        )


def _query(params: Optional[Dict[str, Any]]) -> str:
    if not params:
        return ""
    clean = {key: value for key, value in params.items() if value is not None}
    return ("?" + urlencode(clean)) if clean else ""
