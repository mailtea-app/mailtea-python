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
| `emails.analytics(params=None)` | Aggregate transactional metrics over an optional date window |
| `emails.inbound.list(params=None)` | List received emails in a publication (cursor-paginated) |
| `emails.inbound.get(id)` | Retrieve a received email with body, headers, and attachments |
| `emails.inbound.reply(id, params=None)` | Reply to a received email (threads by construction) |
| `emails.inbound.attachments.list(id)` | List a received email's attachments (signed download URLs) |
| `emails.inbound.attachments.get(id, attachment_id)` | Retrieve one inbound attachment |
| `contacts.create / upsert / list / get / update / delete` | Manage audience contacts (`upsert` = `create`; the endpoint upserts) |
| `posts.create(...)` | Create a newsletter post (draft, or `send=True`) → `{"id": ...}` |
| `posts.send(id, scheduled_at=None)` | Send a draft post to the audience, now or scheduled |
| `posts.send_test(id, params)` | Send a `[TEST]` copy of a post → `{"sent_to", "failed_to"}` |
| `posts.list(params)` | List posts (offset-paginated) → `{"data", "total"}` |
| `posts.get(id, params=None)` | Retrieve a post by id |
| `posts.update(id, params)` | Update a draft post (`subject`, `html`, `text`, `from`, `reply_to`, `name`) |
| `posts.delete(id, params=None)` | Delete a draft post |
| `segments.create / list / get / update / delete` | Manage audience segments |
| `tags.create / list / get / update / delete` | Manage tag definitions (`visibility="public"` → reader-facing topic) |
| `senders.create / list / get / update / delete` | Manage named From identities (`email` immutable) |
| `templates.create / list / get / update / publish / duplicate / delete` | Manage reusable email templates |
| `templates.render(params)` | Render a spec to HTML without saving → `{"html", "text"}` |
| `suppressions.list / add / remove` | Manage the team-wide do-not-send list |
| `suppressions.export()` | Export the whole suppression list as CSV (raw text) |
| `domains.create / list / get / verify / update / delete` | Manage sending domains (add, read DNS records, verify) |
| `domains.tracking.create / list / verify / delete` | Manage CNAME tracking sub-domains under a domain |
| `webhooks.create / list / get / update / delete` | Manage outbound event subscriptions |
| `contact_properties.create / list / update / delete` | Manage custom contact fields (team-scoped) |
| `api_keys.create / list / revoke` | Manage API keys (`settings:write`) |
| `automations.create / list / get / update / delete` | Manage automation graphs (`steps` + optional `connections`) |
| `automations.validate(params)` | Dry-run a graph → `{"valid", "issues"}` (no automation needed) |
| `automations.activate / pause / archive` | Lifecycle (`cancel_runs` defaults **false** on pause, **true** on archive) |
| `automations.versions(id, ...)` / `automations.version(id, version, ...)` | List stored versions; retrieve one with its graph |
| `automations.metrics(id, params=None)` | Per-step funnel counts and branch splits (test runs excluded) |
| `automations.test(id, params)` | One test run against a real contact — **sends real, billed email** |
| `automation_runs.list / get / cancel` | Inspect and cancel runs (a run pins the version it started on) |
| `events.send(params)` | Record a custom event → `{"enrolled_automations", "resumed_runs"}` |
| `events.list(params)` | List recorded events (cursor-paginated) |
| `event_definitions.create / list / get / update / delete` | Manage the event catalog (`name` immutable) |

Payloads follow the REST wire format (`reply_to`, `scheduled_at`, …), passed as
keyword arguments or a plain dict. Errors raise `MailteaError` with `status`,
`details`, and `request_id`.

`emails.send` also accepts `tags`, custom `headers`, `attachments`, and
`scheduled_at`. Attachments carry base64 `content`; set a `content_id` (plus
`content_type`) to embed an inline image referenced by `cid:` in the HTML:

```python
mailtea.emails.send(
    from_="you@yourdomain.com",
    to="recipient@example.com",
    subject="Your receipt",
    html='<p>Thanks!</p><img src="cid:logo" />',
    tags=[{"name": "category", "value": "receipt"}],
    attachments=[
        {"filename": "receipt.pdf", "content": pdf_base64},
        {"filename": "logo.png", "content": logo_base64,
         "content_type": "image/png", "content_id": "logo"},  # inline
    ],
)
```

## Verifying webhooks

Mailtea signs every outbound webhook with [Standard Webhooks](https://www.standardwebhooks.com/).
`verify_webhook_signature` checks the signature and rejects replays. Pass the
**raw** request body (not re-serialized JSON) and the endpoint's `whsec_…`
signing secret:

```python
from mailtea import verify_webhook_signature

ok = verify_webhook_signature(
    secret=signing_secret,                       # whsec_… from webhooks.create
    msg_id=request.headers["webhook-id"],
    timestamp=request.headers["webhook-timestamp"],
    payload=raw_body,                            # exact bytes/string received
    signature_header=request.headers["webhook-signature"],
)
if not ok:
    return 401
```

`sign_webhook(secret, msg_id, timestamp, payload)` produces the same header, handy
for faking deliveries in tests. Both are stdlib-only.

## Develop

```bash
cd sdks/python
python3 -m unittest discover -s tests -t .
```
