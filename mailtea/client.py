from __future__ import annotations

import json
import os
from typing import Any, Optional

from ._resource import wrap as _wrap
from ._transport import Transport, urllib_transport
from .api_keys import ApiKeys
from .automation_runs import AutomationRuns
from .automations import Automations
from .contact_properties import ContactProperties
from .contacts import Contacts
from .domains import Domains
from .emails import Emails
from .errors import MailteaError
from .events import EventDefinitions, Events
from .posts import Posts
from .segments import Segments
from .senders import Senders
from .suppressions import Suppressions
from .topics import Topics
from .templates import Templates
from .webhooks import Webhooks

DEFAULT_BASE_URL = "https://api.mailtea.app"


class Mailtea:
    """The Mailtea client.

    >>> from mailtea import Mailtea
    >>> mailtea = Mailtea(os.environ["MAILTEA_API_KEY"])
    >>> sent = mailtea.emails.send(
    ...     from_="you@yourdomain.com",
    ...     to="recipient@example.com",
    ...     subject="Hello",
    ...     html="<p>Sent with Mailtea.</p>",
    ... )
    >>> sent.id  # responses allow attribute and ["..."] access alike

    Payloads may equally be passed as a single wire-format dict
    (``send({"from": ..., "to": ...})``) — both styles hit the same endpoint.

    The API key may be passed explicitly or read from ``MAILTEA_API_KEY``.
    Self-hosting/local dev: pass ``base_url`` or set ``MAILTEA_API_BASE_URL``.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: Optional[str] = None,
        transport: Optional[Transport] = None,
    ) -> None:
        key = api_key or os.environ.get("MAILTEA_API_KEY")
        if not key:
            raise MailteaError(
                "Missing Mailtea API key. Pass it to Mailtea(api_key) or set the "
                "MAILTEA_API_KEY environment variable.",
                code="missing_api_key",
            )
        self._api_key = key
        self._base_url = (
            base_url or os.environ.get("MAILTEA_API_BASE_URL") or DEFAULT_BASE_URL
        ).rstrip("/")
        self._transport: Transport = transport or urllib_transport

        self.emails = Emails(self._request)
        self.contacts = Contacts(self._request)
        self.posts = Posts(self._request)
        self.segments = Segments(self._request)
        self.senders = Senders(self._request)
        self.suppressions = Suppressions(self._request)
        self.topics = Topics(self._request)
        self.templates = Templates(self._request)
        self.domains = Domains(self._request)
        self.webhooks = Webhooks(self._request)
        self.contact_properties = ContactProperties(self._request)
        self.api_keys = ApiKeys(self._request)
        self.automations = Automations(self._request)
        self.automation_runs = AutomationRuns(self._request)
        self.events = Events(self._request)
        self.event_definitions = EventDefinitions(self._request)

    def _request(self, method: str, path: str, body: Any = None, *, raw: bool = False) -> Any:
        url = self._base_url + path
        headers = {"Authorization": "Bearer " + self._api_key}
        data: Optional[bytes] = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(body).encode("utf-8")

        response = self._transport(method, url, headers, data)
        request_id = response.headers.get("x-request-id")

        if response.status >= 400:
            message = "HTTP {0}".format(response.status)
            details = None
            # Machine-readable code from the API, when it sends one (e.g.
            # ``marketing_plan_required`` on 402). Branching on ``code`` survives
            # a copy change to the message.
            code = None
            try:
                parsed = json.loads(response.text)
                if isinstance(parsed, dict):
                    message = parsed.get("error") or message
                    details = parsed.get("details")
                    raw_code = parsed.get("code")
                    code = raw_code if isinstance(raw_code, str) else None
            except ValueError:
                pass  # non-JSON body — keep the status-line message
            raise MailteaError(
                message,
                status=response.status,
                code=code,
                details=details,
                request_id=request_id,
            )

        if response.status == 204 or not response.text:
            return None
        # A few endpoints (e.g. suppressions export) return non-JSON bodies —
        # hand back the raw text untouched instead of parsing it.
        if raw:
            return response.text
        # Responses are dicts that also allow attribute access
        # (email["id"] and email.id both work).
        return _wrap(json.loads(response.text))
