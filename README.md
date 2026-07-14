# mailtea (Python)

The official Python SDK for [Mailtea](https://mailtea.app) — a thin, zero-dependency
wrapper over the [REST API](https://api.mailtea.app). Python 3.9+.

## Install

```bash
pip install mailtea
```

## Usage

```python
import os
from mailtea import Mailtea

mailtea = Mailtea(os.environ["MAILTEA_API_KEY"])

sent = mailtea.emails.send(
    from_="you@yourdomain.com",
    to="recipient@example.com",
    subject="Hello from Mailtea",
    html="<p>Your first email, sent with <strong>Mailtea</strong>.</p>",
)
print(sent.id)

email = mailtea.emails.get(sent.id)
print(email.status)
```

The API key can be passed to `Mailtea(api_key)` or read from `MAILTEA_API_KEY`.
Self-hosting or local dev? pass `base_url=` or set `MAILTEA_API_BASE_URL`.

Every method equally accepts a single wire-format dict — handy when you already
hold the JSON payload:

```python
sent = mailtea.emails.send({
    "from": "you@yourdomain.com",
    "to": "recipient@example.com",
    "subject": "Hello from Mailtea",
    "html": "<p>Your first email, sent with <strong>Mailtea</strong>.</p>",
})
print(sent["id"])  # responses support ["..."] and attribute access alike
```

Keyword arguments use snake_case wire names; a trailing underscore escapes
Python reserved words (`from_=` → `"from"`).

## API

| Method | Description |
| --- | --- |
| `emails.send(params)` | Send a transactional email → `{"id": ...}` |
| `emails.batch(emails)` | Send up to 100 emails → `{"data": [{"id": ...}]}` |
| `emails.get(id)` | Retrieve an email and its delivery status |
| `emails.list(params=None)` | List emails → `{"data", "total", "limit", "offset", "has_more"}` |
| `emails.update(id, params)` | Reschedule a scheduled email |
| `emails.reschedule(id, scheduled_at)` | Convenience wrapper over `update` |
| `emails.cancel(id)` | Cancel a scheduled email |
| `contacts.create / upsert / list / get / update / delete` | Manage audience contacts (`upsert` = `create`; the endpoint upserts) |
| `posts.create(...)` | Create a newsletter post (draft, or `send=True`) → `{"id": ...}` |
| `posts.send(id, scheduled_at=None)` | Send a draft post to the audience, now or scheduled |
| `posts.send_test(id, params)` | Send a `[TEST]` copy of a post → `{"sent_to", "failed_to"}` |
| `segments.create / list / get / update / delete` | Manage audience segments |
| `tags.create / list / get / update / delete` | Manage tag definitions |
| `domains.create / list / get / verify / update / delete` | Manage sending domains (add, read DNS records, verify) |
| `domains.tracking.create / list / verify / delete` | Manage CNAME tracking sub-domains under a domain |
| `webhooks.create / list / get / update / delete` | Manage outbound event subscriptions |
| `contact_properties.create / list / update / delete` | Manage custom contact fields (team-scoped) |
| `api_keys.create / list / revoke` | Manage API keys (`settings:write`) |

Payloads follow the REST wire format (`reply_to`, `scheduled_at`, …), passed as
keyword arguments or a plain dict. Errors raise `MailteaError` with `status`,
`details`, and `request_id`.

## Develop

```bash
cd sdks/python
python3 -m unittest discover -s tests -t .
```
