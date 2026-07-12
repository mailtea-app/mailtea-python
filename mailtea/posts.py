from __future__ import annotations

from typing import Any, Callable, Dict
from urllib.parse import quote

RequestFn = Callable[..., Any]


class Posts:
    """The ``posts`` resource (newsletter posts/issues). Access via ``mailtea.posts``.

    Payloads are plain dicts matching the REST wire format (snake_case keys like
    ``reply_to``).
    """

    def __init__(self, request: RequestFn) -> None:
        self._request = request

    def send_test(self, id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send a TEST copy of a post to specific recipients to check it before
        subscribers see it. Renders the post exactly as a subscriber would receive
        it and delivers a one-shot ``[TEST]`` email — it does NOT send to the
        audience.

        ``params`` takes ``recipients`` (up to 10), ``from`` (must use a verified
        domain), and optional ``reply_to``. Returns ``{"sent_to": [...], "failed_to": [...]}``.
        """
        return self._request(
            "POST", "/v1/posts/" + quote(str(id), safe="") + "/test", params
        )
