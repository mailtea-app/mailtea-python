from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Union
from urllib.parse import quote, urlencode

RequestFn = Callable[..., Any]
Recipients = Union[str, List[str]]


class Emails:
    """The ``emails`` resource. Access via ``mailtea.emails``.

    Payloads are plain dicts matching the REST wire format (snake_case keys like
    ``reply_to`` and ``scheduled_at``).
    """

    def __init__(self, request: RequestFn) -> None:
        self._request = request

    def send(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send a transactional email. Provide ``html``/``text`` OR a ``template``.

        Returns ``{"id": ...}``.
        """
        return self._request("POST", "/v1/emails", params)

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

    def list(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List emails (most recent first). Optional filters: ``status``, ``tag_name``,
        ``tag_value``, ``from_date``, ``to_date``, ``limit``, ``offset``."""
        return self._request("GET", "/v1/emails" + _query(params))

    def update(self, id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update a scheduled email (currently only ``scheduled_at``)."""
        return self._request("PATCH", "/v1/emails/" + quote(str(id), safe=""), params)

    def reschedule(self, id: str, scheduled_at: str) -> Dict[str, Any]:
        """Convenience wrapper over :meth:`update` for the reschedule case."""
        return self.update(id, {"scheduled_at": scheduled_at})

    def cancel(self, id: str) -> Dict[str, Any]:
        """Cancel a scheduled email before it sends."""
        return self._request("POST", "/v1/emails/" + quote(str(id), safe="") + "/cancel")


def _query(params: Optional[Dict[str, Any]]) -> str:
    if not params:
        return ""
    clean = {key: value for key, value in params.items() if value is not None}
    return ("?" + urlencode(clean)) if clean else ""
