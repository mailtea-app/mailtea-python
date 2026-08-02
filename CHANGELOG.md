# Changelog

All notable changes to the `mailtea` Python package are documented here.

## Unreleased

### Added

- **`MailteaError.code` is now populated from the API's error body.** It has always existed for client-side failures (`missing_api_key`); it was never filled in for HTTP errors, so branching on a specific API error meant matching on `err.message` — which breaks the day the copy changes. Now, when the API sends a `code` alongside `error`, the client carries it through:

  ```python
  try:
      client.contacts.list(publication_id="pub_123")
  except MailteaError as err:
      if err.code == "marketing_plan_required":
          ...  # the team is on a transactional-only plan
  ```

  Purely additive: `code` stays `None` for errors that carry no code, and `message`, `status`, `details` and `request_id` are unchanged.

### Changed

- **Marketing endpoints answer `402` on a transactional-only plan.** Server-side change, no Python change — recorded because it is a new failure mode for existing calls. `client.contacts`, `contact_properties`, `segments`, `topics`, `posts` and `automations` raise `MailteaError` with `status=402` and `code="marketing_plan_required"` when the API key belongs to a team on a transactional-column SKU (`hobby`, `pro_25k`, `pro_50k`, `pro_100k`, `scale_250k`, `scale_500k`, `scale_1m`). `emails`, `domains`, `senders`, `suppressions`, `templates`, `events`, `webhooks` and `api_keys` are unaffected on every plan. Nothing is deleted while a plan is transactional-only — upgrading to the matching `_full` SKU restores access.

## 0.6.0 (2026-07-29)
### Changed

- **BREAKING — `client.tags` is now `client.topics`** and targets `/v1/topics`; the module moved from `mailtea/tags.py` to `mailtea/topics.py` and the class from `Tags` to `Topics`. Method signatures are unchanged. `object` on the returned resource is `"topic"`. Topic ids keep their `tag_` prefix — opaque and permanent.
  The `tags` argument on `emails.send` and the `tag_name` / `tag_value` filters on `emails.list` are the Resend-compatible transactional metadata field, a different concept, and are **unchanged**.
- **Webhook events** `contact.tag_subscribed` / `contact.tag_unsubscribed` are now `contact.topic_subscribed` / `contact.topic_unsubscribed`, with `topic_id` in place of `tag_id`.
- **Template variable names are validated server-side.** `templates.create()` and `templates.update()` forward `variables` verbatim, and the API now refuses a key outside `^[A-Za-z_$@][A-Za-z0-9_$@.-]*$` (1–50 chars) with a `400`; one invalid key fails the whole write. No Python change — the payload is a wire-format dict and the refusal arrives as an ordinary API error. Recorded here because a name outside the rule used to be accepted, stored, and returned by `templates.get()` looking declared, and then substituted nowhere at send time: `Hi {2nd name},` reached the inbox with its braces. Dots address into send context (`contact.first_name`) and dashes are legal (`plan-tier`); pipes, spaces, braces and a leading digit are not.

### Added

- **`templates.versions(id, publication_id=..., limit=...)`** — a template's design history, newest first. Entries are metadata only (`version`, `origin` — `"edit"` / `"publish"` / `"restore"` —, `restored_from_version`, `format`, `name`, `sealed`, `is_current`, timestamps, `author`), never the design document itself, which one entry alone can carry half a megabyte of. `is_current` marks the design the template is serving right now, which is not always the newest entry: a metadata-only update touches the template without recording a version. The reply also carries `retention` — only the newest `max_versions` are kept, and consecutive edits by the same author within `coalesce_window_seconds` collapse into one entry.
- **`templates.restore_version(id, version, publication_id=...)`** — put an older design back. It is a content write, so the template **returns to draft**: automations and the API stop sending it until `templates.publish` is called again, and the reply's `unpublished` says whether that just happened. History is forward-only — the design being replaced is recorded as its own version first and the restored design is appended as the new newest one, so a restore is undone by restoring the entry directly above it. Restoring the design that is already current writes nothing and returns `restored: False` with `reason: "identical"`, so a no-op restore cannot unpublish a live template; a version that has aged out of retention raises with `code` `template_version_not_found`.

## 0.5.0 (2026-07-27)

### Added

- **Designed templates — `format: "editor"`.** `templates.create` and `templates.update` accept `editor_doc`, the TipTap document the Visual Email Designer writes, and the server renders and stores the email HTML from it. This is what makes a template designed in Mailtea Studio and one authored from code the same record: previously the design source lived only in the operator's browser and the API could only take raw `html` or a json-render `spec`. Do **not** pass `html` alongside `editor_doc` — the HTML is derived, and an update that tries it is refused with `editor_template_html_not_accepted`.
- **The fidelity sidecars `html` cannot carry** — `style_profile`, `mailtea_theme` and `global_css`, plus the library metadata `category`, `preview_image_url` and `tags`. On update the four clearable fields take `None` to clear, the same way `subject` and `reply_to` already do.
- **`templates.unpublish(id, publication_id=...)`** — the retraction half of `publish`. Publishing was one-way: the only way to take a template out of circulation was to delete it or edit its body. `status` returns to `draft` and the body is untouched; `published_at` is kept, because it records that the template *was* published, which is history rather than current state.

### Changed

- `templates.render` now actually substitutes the `variables` map it has always accepted. The server parsed the map and discarded it, so a preview came back full of raw `{{placeholders}}` while every other render path substituted. No signature change — the same call now returns the rendered result it documented.
- `templates.render` now requires the `templates:read` scope. It was the only template route with no scope check at all. Keys minted from the `read_only` or `sending_access` presets hold no `templates:*` scope and will now receive a `403`; they could not list, read or create templates before either.

## 0.4.0 (2026-07-27)

### Added

- **Automations resource** — `client.automations.create / list / get / update / delete`, the lifecycle verbs `activate / pause / archive`, version history via `versions / version`, plus `metrics` and `test`. An automation is a versioned graph of `steps` + `connections` with no stored coordinates, so it is fully authorable from Python. `connections` is **optional**: omit it and the steps link in array order; it becomes required as soon as the graph contains a `condition` or `wait_for_event` step, which otherwise fails with `connections_required_for_branching`.
- **Graph validation without saving** — `automations.validate(...)` dry-runs a graph that does not exist yet, and `validate_only=True` on `create` / `update` returns the same coded `issues` list a real failure would, writing nothing. Each issue carries a stable `code`, a `severity`, and the offending `step_key` / `path`: warnings never block saving, errors block activation.
- **Automation runs resource** — `client.automation_runs.list / get / cancel`. Run detail is self-contained: it returns the graph the run is pinned to (which may not be the live one), the ordered step timeline and the waiting state.
- **Events resources** — `client.events.send / list` for custom event ingest (opt-in `create_contact`, `idempotency_key`, and the `enrolled_automations` / `resumed_runs` fan-out counts in the reply), and `client.event_definitions.create / list / get / update / delete`. The definition detail returns `inferred_properties` with per-key type, sample count and **coverage**, computed on read over the last 500 events.

- **`search` on `emails.list`** — a case-insensitive substring match over recipient, sender and subject, applied server-side before pagination rather than to the current page. Shipped server-side on 2026-07-22, one day after 0.3.0 went out, so this is the first published release that carries it.

### Documentation

- `contacts.list` now documents its `search` filter. The filter itself is not new — it has worked through the keyword passthrough since the resource shipped — it was simply never written down.

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
