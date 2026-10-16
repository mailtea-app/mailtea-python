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
        attachments. ``reply_to`` lists where the sender asked replies to go (a
        reply goes to the first one by default). The arrival checks are
        ``spam_verdict``, ``virus_verdict``, ``spf_verdict``, ``dkim_verdict``
        and ``dmarc_verdict`` (``PASS``, ``FAIL``, ``GRAY``,
        ``PROCESSING_FAILED`` or None), and ``attachments_withheld`` is True
        when the files were kept back after a failed virus check."""
        return self._request("GET", _BASE + "/" + quote(str(id), safe=""))

    def reply(self, id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Reply to a received email. Threading headers and the ``Re: ``
        subject default are server-derived, and the reply goes to the
        original's Reply-To when it is exactly one valid address, else its From
        when that is exactly one valid address, else it raises on a 422
        ``no_reply_target``. ``to`` (a string or a list) may name only the From
        or a single-address Reply-To entry; anything else raises on a 422
        ``reply_target_not_allowed``. Pass the content (``html``/``text``)
        and optionally ``from``, ``subject``, ``cc``, ``bcc``, ``attachments``
        (a list of ``{"filename", "content", "content_type", "content_id"}``
        with ``content`` base64; up to 20 files, 6 MiB together, and the whole
        message must build under the provider's limit), ``headers`` (only
        ``Auto-Submitted`` and ``X-Auto-Response-Suppress``) and
        ``idempotency_key``. A plan limit raises on a 403 whose ``code`` is
        ``daily_cap``, ``monthly_cap`` or ``ramp_cap``. Returns the resulting
        transactional email's ``id`` and ``status``; a retry with the same key
        answers 202 while the reply is queued and 200 once sent. If the reply
        failed, the retry raises on a 409 whose ``code`` is ``reply_failed``,
        and the same key then makes a fresh reply."""
        return self._request(
            "POST",
            _BASE + "/" + quote(str(id), safe="") + "/reply",
            _body(params, kwargs),
        )
