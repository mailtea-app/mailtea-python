from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Union
from urllib.parse import quote

from ._resource import body as _body, query as _query
from .inbound import InboundEmails

RequestFn = Callable[..., Any]
Recipients = Union[str, List[str]]


class Emails:
    """The ``emails`` resource. Access via ``mailtea.emails``.

    Every method accepts the payload as a wire-format dict, as keyword
    arguments, or both (snake_case keys like ``reply_to``; use ``from_=`` as
    the keyword form of ``"from"``).
    """

    def __init__(self, request: RequestFn) -> None:
        self._request = request
        #: Inbound (received) emails: list, get, reply, and attachments.
        self.inbound = InboundEmails(request)

    def send(self, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Send a transactional email. Provide ``html``/``text`` OR a ``template``.

        >>> mailtea.emails.send(from_="a@b.co", to="c@d.co", subject="Hi", html="<p>Hi</p>")

        Set the From with exactly one of ``from_`` (a ``Name <email>`` string) or
        ``sender_id`` (the id of a named, verified publication sender, which also
        supplies its default ``reply_to``).

        ``to``, ``cc``, ``bcc``, and ``reply_to`` each accept a single address or
        a list. Additional optional fields (wire format, snake_case):

        - ``tags`` — a list of ``{"name": ..., "value": ...}`` for filtering and
          analytics.
        - ``headers`` — a dict of extra custom email headers.
        - ``attachments`` — a list of ``{"filename", "content", ...}`` where
          ``content`` is base64. Set ``content_type`` and a ``content_id`` to
          embed an inline image referenced by ``cid:`` in the HTML; omit
          ``content_id`` for a regular file attachment.
        - ``scheduled_at`` — an ISO 8601 datetime to schedule the send.

        Returns ``{"id": ...}``.
        """
        return self._request("POST", "/v1/emails", _body(params, kwargs))

    def analytics(self, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Aggregate transactional metrics over an optional date window: totals,
        delivered/bounced/open/click counts, per-status counts, and rates.
        Optional filters: ``from_date``, ``to_date`` (ISO 8601)."""
        return self._request("GET", "/v1/emails/analytics" + _query(_body(params, kwargs)))

    def batch(self, emails: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Send up to 100 emails in one request. Returns ``{"data": [{"id": ...}]}``."""
        return self._request("POST", "/v1/emails/batch", emails)

    def get(self, id: str) -> Dict[str, Any]:
        """Retrieve an email with its delivery status and tracking counters.

        Adds a friendly ``status`` alias of the raw ``last_event`` wire field.
        """
        email = self._request("GET", "/v1/emails/" + quote(str(id), safe=""))
        if isinstance(email, dict) and email.get("status") is None:
            email["status"] = email.get("last_event")
        return email

    def list(self, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """List emails (most recent first). Optional filters: ``status``, ``tag_name``,
        ``tag_value``, ``from_date``, ``to_date``, ``limit``, ``offset``."""
        return self._request("GET", "/v1/emails" + _query(_body(params, kwargs)))

    def update(self, id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Update a scheduled email (currently only ``scheduled_at``)."""
        return self._request(
            "PATCH", "/v1/emails/" + quote(str(id), safe=""), _body(params, kwargs)
        )

    def reschedule(self, id: str, scheduled_at: str) -> Dict[str, Any]:
        """Convenience wrapper over :meth:`update` for the reschedule case."""
        return self.update(id, {"scheduled_at": scheduled_at})

    def cancel(self, id: str) -> Dict[str, Any]:
        """Cancel a scheduled email before it sends."""
        return self._request("POST", "/v1/emails/" + quote(str(id), safe="") + "/cancel")
