from __future__ import annotations

from typing import Any, Callable, Dict, Optional
from urllib.parse import quote

from ._resource import body as _body, query as _query

RequestFn = Callable[..., Any]


class Topics:
    """The ``topics`` resource (topic definitions). Access via ``mailtea.topics``.

    Topics are scoped to a publication — pass ``publication_id``. ``create``
    requires ``default_subscription`` (``"opt_in"`` or ``"opt_out"``). This
    manages topic definitions only; assigning topics to contacts is not yet exposed.
    Every method accepts the payload as a wire-format dict, as keyword
    arguments, or both.
    """

    def __init__(self, request: RequestFn) -> None:
        self._request = request

    def create(self, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Create a topic definition. Requires ``publication_id``, ``name``, and
        ``default_subscription`` (``"opt_in"`` or ``"opt_out"``). Optional
        ``description`` and ``visibility`` (``"private"`` by default; ``"public"``
        makes the topic appear on the reader preference page as its own subscription)."""
        return self._request("POST", "/v1/topics", _body(params, kwargs))

    def list(self, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        return self._request("GET", "/v1/topics" + _query(_body(params, kwargs)))

    def get(self, id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        return self._request(
            "GET", "/v1/topics/" + quote(str(id), safe="") + _query(_body(params, kwargs))
        )

    def update(self, id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        merged = _body(params, kwargs)
        return self._request(
            "PATCH",
            "/v1/topics/"
            + quote(str(id), safe="")
            + _query({"publication_id": merged.get("publication_id")}),
            merged,
        )

    def delete(self, id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        return self._request(
            "DELETE", "/v1/topics/" + quote(str(id), safe="") + _query(_body(params, kwargs))
        )
