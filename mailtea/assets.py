from __future__ import annotations

import base64
from typing import Any, Callable, Dict, Optional, Union
from urllib.parse import quote

from ._resource import body as _body, query as _query

RequestFn = Callable[..., Any]


class Assets:
    """The ``assets`` resource (a publication's image library). Access via ``mailtea.assets``.

    An email or site image needs an absolute URL, so this is how a picture that
    is not already in the library gets into one. Pointing an image at a host you
    do not control breaks the day that host moves the file.

    PNG, JPEG, GIF, WebP or SVG, 5 MB per image. SVG is accepted; the public
    asset route serves it under a sandboxing Content-Security-Policy so it
    cannot run script on the publication's domain. The bytes are
    checked against the declared ``content_type``, so a mislabelled file is
    rejected rather than stored.

    ``upload`` accepts ``content`` as raw ``bytes`` and base64-encodes it for
    you, or as an already-encoded ``str``::

        asset = mailtea.assets.upload(
            publication_id="pub_123",
            content=open("hero.png", "rb").read(),
            content_type="image/png",
            filename="hero.png",
        )
        asset["url"]  # -> use as an image block's src
    """

    def __init__(self, request: RequestFn) -> None:
        self._request = request

    def upload(self, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        payload = _body(params, kwargs)
        content: Union[bytes, bytearray, str, None] = payload.get("content")
        if isinstance(content, (bytes, bytearray)):
            payload = {**payload, "content": base64.b64encode(bytes(content)).decode("ascii")}
        return self._request("POST", "/v1/assets", payload)

    def list(self, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """List the library, newest first. Filters: ``publication_id`` (required),
        ``search`` (file name), ``limit`` (1-200, default 100)."""
        return self._request("GET", "/v1/assets" + _query(_body(params, kwargs)))

    def delete(self, id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Retire an asset.

        The stored file is KEPT and its URL keeps resolving, so images inside
        already-sent emails do not break. This hides the asset from the library —
        it does not remove it from any email, template or page referencing it.
        """
        return self._request(
            "DELETE", "/v1/assets/" + quote(str(id), safe="") + _query(_body(params, kwargs))
        )
