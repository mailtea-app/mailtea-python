# Changelog

All notable changes to the `mailtea` Python package are documented here.

## 0.21.0 (2026-10-03)

- Changed (API): `posts.send`, and `posts.create` with `send=True`, now raise
  on a 403 `system_domain_recipient_restricted` (with `restriction`) when the
  team has no verified sending domain and the audience includes anyone outside
  the team, or the post sends from the built-in `*.mailtea.email` address.
  Nothing is sent or scheduled and the post stays a draft; on `posts.create`
  the error body carries the draft's `id`. The send used to be accepted and
  fail a moment later. A broadcast (`kind="broadcast"`) is never published to
  the website, however it is sent. No package change: this is the API's
  behaviour once it is deployed.

## 0.20.0 (2026-10-01)

- Changed (API): `contacts.list(search=...)` with several whole addresses
  separated by commas or spaces now returns exactly those contacts (up to
  200), the same as Mailtea Studio and MCP. A list with an entry that is not
  a whole address is refused with a 400 naming it. Part of an address still
  matches as before. The docstring says so.
- Added: `purpose` on `domains.claims.create` (`"email"`, `"site"` or `"both"`,
  default `"email"`) and on every claim reply. A `site` claim gets no sending
  identity. The package passes it through as it is; this release documents it.
  Needs the API deployed with this change.
- Added: `segment_id` on `posts.create` and `posts.update` (`None` clears it
  on update) and on every post reply, to send a post to one segment of its
  publication instead of all active contacts. `inactive_days` on
  `segments.create` and `segments.update` (`None` clears it) and on every
  segment reply: contacts with no open or click in the last N days (1 to
  3650), counting contacts who never engaged, which is the silent cohort and
  not engaged readers. The package passes both through as it is; this release
  documents them. They need the API deployed with this change.
- Changed: `segments.delete` documents that a segment a draft, scheduled or
  sending post targets cannot be deleted: it raises `MailteaError` with
  status 409 and `code` `segment_in_use`. Deleting one used to send those
  posts to everyone.

## 0.19.0 (2026-09-29)

- Changed: template history records the sender. Each entry from
  `templates.versions()` carries `from` (read it as `entry["from"]`),
  `reply_to` and `sender_recorded`, an update that changes only the From or
  Reply-To records a version (or folds into the open one, like any edit), and
  `templates.restore_version()` brings the version's From and Reply-To back
  with the design. A version with `sender_recorded` `False` was recorded
  before this change and leaves the current From and Reply-To alone when
  restored. The behaviour comes from the API and reaches every package version
  on deploy; this release updates the docstrings.

## 0.18.0 (2026-09-28)

- Added: optimistic-concurrency tokens for editing over an API that may also
  be edited in Mailtea Studio or by another agent. `templates.update` and
  `templates.publish` accept `base_revision` (read from a template's
  `revision`, now on every template reply); a stale value answers with
  `MailteaError` (`code` `stale_write`, the response body also carrying
  `current_revision`) and nothing is saved. `automations.update` accepts
  `base_version` the same way for graph writes (`steps`), answering `code`
  `stale_version`. `posts.update` accepts `base_updated_at` (read from a
  post's `updated_at`, now also returned by `posts.update` itself), answering
  `code` `stale_write` with `current_updated_at`. All three are optional;
  omit them for today's unconditional write.
- Changed: `posts.create` / `posts.update` keep the `from` (keyword `from_=`)
  and `reply_to` you pass, and `posts.get` returns them (`None` when the named
  sender or the publication default decides). `name` is only the post's
  internal name and no longer overwrites the subject. `posts.update` changes
  only the fields you pass; `""` clears `name`, `from` or `reply_to`.
- Note: a `from` that is not on one of the publication's verified sending
  domains is refused with a 422, and `reply_to` must be a valid address.

- Docs: `automations.activate` lists the two cloud-only `no_verified_sender`
  reasons, `CUSTOM_DOMAIN_REQUIRED` and the new `BUILT_IN_SENDER` (a step sends
  from the built-in `{slug}.mailtea.email` address). No runtime change.
- Breaking: `posts.create()` with `template_id` now HTML-escapes the
  `variables` you pass, the same as every other send. HTML passed in a
  `{{key}}` value now arrives as visible text, and a value you escaped
  yourself arrives double-escaped. Put `{{{key}}}` in the template where a
  value is meant to be raw HTML. Variables are now filled in both the
  `{{key}}` and Visual Email Designer `{key}` forms. A declared variable you
  do not pass stays in the post with its `fallback_value`, so the broadcast
  gives each recipient their own value or that fallback, and undeclared tokens
  like `{{contact.first_name}}` are left for the broadcast too. The post keeps
  the template's published page style, is wrapped in that page, and has its
  show-if blocks decided per recipient when it is sent. Before, only the
  variables you passed were replaced, raw, and only in `{{key}}` form. It uses
  the template's published version; Mailtea Studio's "Use template" starts
  from the latest saved design instead.
- Changed: `templates.update()` and `templates.restore_version()` no longer
  move a published template back to draft. The template keeps its published
  status, and automations and the API keep sending its published version until
  `templates.publish()` is called again. The template's `from` and `reply_to`
  are part of the published version too, so a new sender or reply-to address
  reaches sends only after the next publish. `templates.unpublish()` is now
  the only way to stop a published template sending, short of deleting it, and
  it drops the stored published version so the next publish starts from the
  current content.
- Added: `has_unpublished_versions` on every returned template. True only when
  the template is published and its saved content (From, Reply-To and the
  style profile included) differs from the published version.
- Added: `is_published` on each template version entry: true for the one entry
  automations and the API are sending now. `is_current` is now described as
  what it is: the entry that matches the working copy (the saved design being
  edited), not necessarily what is sending. `is_published` is false on every
  entry of a draft, and on a template published before the field existed until
  it is published again.
- Changed: the `unpublished` field on the update and restore replies is kept
  for compatibility and is now always `False`. Check
  `has_unpublished_versions` (or the reply's `message`) instead.
- Changed (API behavior): a template variable's `fallback_value` can no longer
  contain `{` or `}`. Creating a template with one, or changing a fallback
  to one on update, is a 400 ("Fallbacks can't contain { or }."). A value
  the template already stores is accepted unchanged, so a template saved
  before the rule keeps saving. Inline chip fallbacks such as
  `{first_name|Mom & Pop}` now render as written instead of double-escaped.
- Changed (API behavior): saving an active automation is refused only when the
  edit adds an error the live version does not already have. The 422
  `active_graph_invalid` reply's `issues` lists just those new problems.
  Before, any error refused the save, even one the live version already had.
  Starting refuses every error as before, except an `unknown_step_ref` at a
  `config.*` path or a trigger `missing_branch` that the version the
  automation last ran on already had, so pausing and starting an unchanged
  automation keeps working. Issues the last live version already had come back
  with `pre_existing: true`.
- Added (API behavior): issue objects carry `field`, what a rule reads (the
  rule's `field`, or the path in a `{"var": ...}` value, e.g.
  `steps.welcome.opened`) when the issue is about one.
- Changed (API behavior): two issues are the same problem when their code and
  step match, and their `field` or, when there is none, their `path`. Moving
  a rule, by removing a rule beside it or putting it in a group, no longer
  makes a problem the live version already had look new. An error is
  `pre_existing` only if the live version had an error there, not a warning.
- Changed (API behavior): `validate_only` on an active automation answers the
  way the save would. A trigger change is a 422 `trigger_locked_while_active`,
  a change that adds a problem is a 422 `active_graph_invalid` listing only
  the new problems, and otherwise issues come back with `pre_existing` marked
  against the version live now. Before, it returned every issue unmarked.
- Changed (API behavior): changing the trigger (its type or key) of an active
  automation is now refused with 422 `trigger_locked_while_active`. Pause it
  first; draft and paused automations can still change their trigger. Before,
  the change was accepted.
- Added (API behavior): new validation rules. A trigger with nothing after it
  is a `missing_branch` error at `branches.next`. A rule or `{"var": ...}`
  value that reads `steps.<key>.*` for a step that isn't in the automation is
  an `unknown_step_ref` error at that `config.*` path, or a warning when the
  `{"var": ...}` has a `default`. A rule or value that reads
  `event.properties.*` when the automation does not start from an app event is
  the new warning `event_field_without_event_trigger`.
- Changed (API, no client change needed): `emails.send(template=...)` may
  leave out `subject`, `from_` and `sender_id`. The template's published
  subject is used, and its sender is the publication's default sender, then
  the template's own From. The `send` docstring now says so.
- Behaviour (API): the template's variables fill the subject with the same
  values and fallbacks as the body.

## 0.12.0 (2026-09-15)

- Added: test mode. `api_keys.create(name=..., mode="test")` mints a test key
  (prefixed `mt_test_`) whose sends are validated, recorded and webhook-emitting
  but never delivered, so CI can run against production Mailtea with your real
  code and your real webhook handler. A test key is **not** a data sandbox — it
  reads and writes your real contacts, templates, senders and webhooks. Only
  delivery is simulated.
- Added: `emails.list(mode="test")` reads test-mode mail, and every email
  carries `mode`. There is no mixed view: a test key reads only test emails and
  a live key only live ones.
- Reserved recipients on `test.mailtea.email` force an outcome: `delivered@`,
  `bounced@`, `complained@`, `delayed@`, `failed@`. The first `to` recipient
  decides; anything else is delivered.
- Note: `mode` is never accepted on a send. The key decides.

## 0.11.0 (2026-09-10)

- Changed: `automations.activate()` documents the `no_verified_sender` refusal.
  A 422 with that code means a `send_email` step has no sender it can send
  from; `reason` (`NO_SENDER`, `DOMAIN_NOT_VERIFIED`, `WRONG_PURPOSE`,
  `DKIM_NOT_VERIFIED` or `INVALID_FROM`) says which, and `steps[]` names every
  blocking step. Previously only `automation_invalid` was documented.
- Added: `domains.update(id, tracking_subdomain=None)` removes a tracking
  subdomain. The domain's links go back to being served from the Mailtea host.
  Links in mail you have already sent point at the old hostname and stop
  resolving — there is no way to reinstate them. The `None` reaches the wire as
  an explicit `null`, so omitting the key and passing `None` are different
  requests. An empty string is neither: it is refused with
  `tracking_subdomain_invalid`.
- Changed: the `MX` row in `records` now reports what the last verify found,
  instead of reading `pending` on every request but the verify itself. A domain
  nobody has verified reads `not_started`.

## 0.10.0 (2026-09-03)

- Added: `domains.claims` — `create()`, `get()`, `verify()` and `cancel()`. When
  adding a domain is refused with code `domain_held_elsewhere`, another
  publication holds the host; publish one TXT record to prove you control its
  DNS and the domain moves to you.
- Documented: `domains.create()` takes `region` (fixed at creation), `tls` and
  `tracking_subdomain`, and `domains.list()` filters on `region` and `status`.
  The resource forwards whatever you pass, so these worked already — this
  release is where they are stated and covered by tests.

- Added: `contacts.set_property_values()` and `contacts.list_property_values()`.
  These write and read the per-contact values behind `{{contact.<key>}}` merge
  tags — previously only possible from the dashboard, so a script could define a
  property and never fill it in. Identify each value by `key` (the name in your
  template) or `property_id`, not both; an empty `value` clears it and restores
  the property's `fallback_value`.

- Documented: `assets.upload` accepts SVG (`image/svg+xml`); the docstring said it
  was refused. The API has accepted it, served under a sandboxing CSP, since the
  asset library shipped. Docs-only, no behaviour change.

## 0.9.1 (2026-08-25)

- Documented: the API now enforces your plan's analytics retention window on
  `from_date`. It is clamped to 30 days on most plans and 90 on Scale and
  Enterprise; a value reaching further back returns data from the start of that
  window rather than an error, and omitting it returns the window rather than
  all time. No code change is required — this release only makes the behaviour
  visible where you read it.
- Changed: the list and analytics responses now report the window actually used
  in `from_date`, so a clamped request is visible rather than silently short.
- Changed: `emails.list()` and `emails.analytics()` docstrings carry it.

## 0.9.0 (2026-08-24)

- Changed: every transactional webhook's `to` is the delivered envelope, and
  `dropped_recipients` names anyone filtered out. Also on the email record from
  `emails.get`.

- Added: `domains.update(..., custom_return_path=...)` delegates a subdomain as
  the envelope sender so SPF aligns with your own domain, and every domain shape
  carries `custom_return_path` / `custom_return_path_status`. Mail keeps sending
  on the default return-path until the delegated DNS resolves.

- Changed: `to`, `cc` and `bcc` are validated as email addresses. A malformed
  recipient returns `400` rather than being accepted and failing at the
  provider. The `"Name" <address>` form keeps working.

- Added: `tracking_open` and `tracking_click` on `emails.send` and
  `emails.batch` — send a message without an open pixel or without rewritten
  links. A sending domain with tracking switched off cannot be overridden from
  a send.

## 0.8.0 (2026-08-22)

- Added: `image/svg+xml` is an accepted asset type for `assets.upload` — SVG
  logos and marks upload like any raster. The public asset route serves every
  asset with `Content-Security-Policy: sandbox`, which is what makes hosting
  SVGs safe: scripts inside one never execute, in an `<img>` or navigated to
  directly.


## 0.7.0 (2026-08-06)

### Added

- **`client.assets` — the publication's image library.** `upload`, `list` and
  `delete`. An email or site image block takes an absolute URL, so until now a
  Python caller could compose a whole newsletter and had no way to put a picture
  in it.

  ```python
  asset = client.assets.upload(
      publication_id="pub_123",
      content=open("hero.png", "rb").read(),   # bytes, base64-encoded for you
      content_type="image/png",
      filename="hero.png",
  )
  asset["url"]  # -> use as an image block's src
  ```

  `content` also accepts an already-base64 `str`. PNG, JPEG, GIF or WebP, 5 MB
  per image, 500 MB per publication. **SVG is refused** — it can carry script and
  the file is served from a Mailtea domain — and the bytes are checked against
  the declared `content_type`. `delete` hides an asset from the library but KEEPS
  the file resolving, so images in already-sent emails do not break.

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
