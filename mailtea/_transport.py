from __future__ import annotations

import urllib.error
import urllib.request
from typing import Callable, Dict, Iterable, NamedTuple, Optional, Tuple


class HttpResponse(NamedTuple):
    status: int
    headers: Dict[str, str]
    text: str


# (method, url, headers, body) -> HttpResponse. Injectable so tests need no network.
Transport = Callable[[str, str, Dict[str, str], Optional[bytes]], HttpResponse]


def _lower_headers(items: Iterable[Tuple[str, str]]) -> Dict[str, str]:
    return {key.lower(): value for key, value in items}


def urllib_transport(
    method: str, url: str, headers: Dict[str, str], body: Optional[bytes]
) -> HttpResponse:
    """Default transport built on the standard library — no third-party deps."""
    request = urllib.request.Request(url=url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request) as response:  # noqa: S310 (trusted base URL)
            return HttpResponse(
                response.status,
                _lower_headers(response.headers.items()),
                response.read().decode("utf-8"),
            )
    except urllib.error.HTTPError as error:
        text = error.read().decode("utf-8") if error.fp is not None else ""
        return HttpResponse(error.code, _lower_headers(error.headers.items()), text)
