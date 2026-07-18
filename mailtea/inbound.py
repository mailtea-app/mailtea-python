from __future__ import annotations

from typing import Any, Callable, Dict, Optional
from urllib.parse import quote

from ._resource import body as _body, query as _query

RequestFn = Callable[..., Any]

_BASE = "/v1/emails/inbound"


class InboundAttachments:
    """Attachments on a received email. Access via
    ``mailtea.emails.inbound.attachments``.

    Each returned object carries a short-lived signed ``download_url``.
    """

    def __init__(self, request: RequestFn) -> None:
        self._request = request

    def list(self, id: str) -> Dict[str, Any]:
        """List an inbound email's attachments, each with a signed download URL."""
        return self._request(
            "GET", _BASE + "/" + quote(str(id), safe="") + "/attachments"
        )

    def get(self, id: str, attachment_id: str) -> Dict[str, Any]:
        """Retrieve a single inbound attachment with a signed download URL."""
        return self._request(
            "GET",
            _BASE
            + "/"
            + quote(str(id), safe="")
            + "/attachments/"
            + quote(str(attachment_id), safe=""),
        )


class InboundEmails:
    """Inbound (received) emails. Access via ``mailtea.emails.inbound``.

    List and retrieve mail delivered to your receiving domains, download
    attachments, and :meth:`reply` — which threads correctly by construction and
    reuses the transactional send pipeline. Scoped to a publication — pass
    ``publication_id`` to :meth:`list`. Every method accepts the payload as a
    wire-format dict, as keyword arguments, or both.
    """

    def __init__(self, request: RequestFn) -> None:
        self._request = request
        #: Attachments on a received email.
        self.attachments = InboundAttachments(request)

    def list(self, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """List received emails in a publication (most recent first),
        cursor-paginated. Takes ``publication_id``, optional ``limit`` (1-100,
        default 20) and ``cursor``."""
        return self._request("GET", _BASE + _query(_body(params, kwargs)))

    def get(self, id: str) -> Dict[str, Any]:
        """Retrieve a single received email, including its body, headers, and
        attachments."""
        return self._request("GET", _BASE + "/" + quote(str(id), safe=""))

    def reply(self, id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Reply to a received email. The reply target (``to``), threading
        headers, and the ``Re: `` subject default are all server-derived — pass
        only the content (``html``/``text``, and optionally ``from``, ``subject``,
        ``cc``, ``bcc``, ``idempotency_key``). Returns the resulting transactional
        email's ``id`` and ``status``."""
        return self._request(
            "POST",
            _BASE + "/" + quote(str(id), safe="") + "/reply",
            _body(params, kwargs),
        )
