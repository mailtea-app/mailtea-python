# Changelog

All notable changes to the `mailtea` Python package are documented here.

## 0.3.0 (2026-07-21)

### Added

- **Senders resource** — `client.senders.list / create / get / update / delete` for named from-identities on verified sending domains. `emails.send` documents `sender_id` as an alternative to `from_` (pass exactly one of the two).
- **Suppressions resource** — `client.suppressions.list / add / remove` for the org-wide do-not-send list, plus `suppressions.export()` returning the full list as CSV text.
- **Templates resource** — `client.templates.render / create / list / get / update / publish / duplicate / delete`; `render(spec)` previews a template spec as `{html, text}` without saving anything.
- **Full posts CRUD** — `posts.list` (offset-based), `posts.get`, `posts.update`, `posts.delete`.

### Documentation

- `tags.create` documents `description` and `visibility` (`"public"` makes the tag a reader-facing topic).
- `posts.create` documents `kind` (`newsletter` | `broadcast`).

## 0.2.0 (2026-07-18)

- Webhook signature verification helpers, the inbound email resource (list, get, reply, attachments), and email analytics.

## 0.1.2 (2026-07-14)

- Aligned the SDK surface with the documented interface.

## 0.1.0 (2026-06-22)

- Initial public release: emails, contacts, posts, segments, tags, domains, webhooks, contact properties, API keys.
