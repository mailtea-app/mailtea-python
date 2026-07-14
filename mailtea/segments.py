from __future__ import annotations

from typing import Any, Callable, Dict, Optional
from urllib.parse import quote

from ._resource import body as _body, query as _query

RequestFn = Callable[..., Any]


class Segments:
    """The ``segments`` resource. Access via ``mailtea.segments``.

    Audience segments are scoped to a publication — pass ``publication_id``.
    Every method accepts the payload as a wire-format dict, as keyword
    arguments, or both. To clear a nullable filter on update, pass ``None``
    (e.g. ``status_filter=None``); omit the key to leave it unchanged.
    """

    def __init__(self, request: RequestFn) -> None:
        self._request = request

    def create(self, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        return self._request("POST", "/v1/segments", _body(params, kwargs))

    def list(self, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        return self._request("GET", "/v1/segments" + _query(_body(params, kwargs)))

    def get(self, id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        return self._request(
            "GET", "/v1/segments/" + quote(str(id), safe="") + _query(_body(params, kwargs))
        )

    def update(self, id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        merged = _body(params, kwargs)
        return self._request(
            "PATCH",
            "/v1/segments/"
            + quote(str(id), safe="")
            + _query({"publication_id": merged.get("publication_id")}),
            merged,
        )

    def delete(self, id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        return self._request(
            "DELETE", "/v1/segments/" + quote(str(id), safe="") + _query(_body(params, kwargs))
        )
