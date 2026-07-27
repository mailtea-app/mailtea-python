from __future__ import annotations

from typing import Any, Callable, Dict, Optional
from urllib.parse import quote

from ._resource import body as _body, query as _query

RequestFn = Callable[..., Any]


class Events:
    """The ``events`` resource (custom product events that trigger automations
    and resume ``wait_for_event`` steps). Access via ``mailtea.events``.

    Events are scoped to a publication — pass ``publication_id``. Every method
    accepts the payload as a wire-format dict, as keyword arguments, or both.
    """

    def __init__(self, request: RequestFn) -> None:
        self._request = request

    def send(self, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Record an event for a contact. Takes ``publication_id``, ``name``, and
        exactly one of ``contact_id`` or ``email`` (both is a 400
        ``contact_reference_conflict``, neither a 400
        ``contact_reference_required``). Optional: ``create_contact``,
        ``properties``, ``occurred_at``, ``idempotency_key``.

        ``create_contact`` is **opt-in** — without it an unresolvable address is
        a 404 ``contact_not_found`` rather than a new contact.

        Returns 202 with ``enrolled_automations`` and ``resumed_runs``. A replay
        of the same ``idempotency_key`` returns the ORIGINAL event id with
        ``replayed: true`` and always reports ``enrolled_automations: 0,
        resumed_runs: 0``. Note that ``resumed_runs: 0`` on a FRESH ingest does
        not prove nothing matched — a run being advanced concurrently is
        invisible for that instant, so read the run itself
        (``mailtea.automation_runs.get``) rather than the counter."""
        return self._request("POST", "/v1/events", _body(params, kwargs))

    def list(self, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """List recorded events (cursor-paginated). Filters: ``publication_id``
        (required), ``name``, ``contact_id``, ``limit``, ``after`` (cursor from a
        previous ``next_cursor``)."""
        return self._request("GET", "/v1/events" + _query(_body(params, kwargs)))


class EventDefinitions:
    """The ``event_definitions`` resource (the catalog of event names a
    publication expects, with optional property schemas). Access via
    ``mailtea.event_definitions``.

    Definitions are scoped to a publication — pass ``publication_id``. They are
    documentation and tooling, not a gate: :meth:`Events.send` accepts an event
    with no definition. Every method accepts the payload as a wire-format dict,
    as keyword arguments, or both.
    """

    def __init__(self, request: RequestFn) -> None:
        self._request = request

    def create(self, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Create an event definition. Takes ``publication_id`` and ``name``,
        plus optional ``description`` and ``schema_json``. The name is
        immutable once created."""
        return self._request("POST", "/v1/event-definitions", _body(params, kwargs))

    def list(self, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """List event definitions (cursor-paginated). Filters:
        ``publication_id`` (required), ``limit``, ``after``. List items carry no
        ``inferred_properties`` — use :meth:`get` for those."""
        return self._request("GET", "/v1/event-definitions" + _query(_body(params, kwargs)))

    def get(self, id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Retrieve one definition. Requires ``publication_id``. Adds
        ``schema_properties`` and ``inferred_properties`` — the latter computed
        on read over the last 500 events, reporting each key's type, sample
        count and **coverage**. Low coverage is the trap: a condition on a key
        present in 3% of events will almost never match."""
        return self._request(
            "GET",
            "/v1/event-definitions/" + quote(str(id), safe="") + _query(_body(params, kwargs)),
        )

    def update(self, id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Update a definition's ``description`` or ``schema_json`` (``None``
        clears the schema back to free-form). ``publication_id`` is required
        (sent as a query parameter). ``name`` is immutable — sending it is a 400
        ``event_name_immutable``, not a silently dropped rename."""
        merged = _body(params, kwargs)
        publication_id = merged.pop("publication_id", None)
        return self._request(
            "PATCH",
            "/v1/event-definitions/"
            + quote(str(id), safe="")
            + _query({"publication_id": publication_id}),
            merged,
        )

    def delete(self, id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Delete an event definition. Requires ``publication_id``. Events
        already recorded under that name are untouched."""
        return self._request(
            "DELETE",
            "/v1/event-definitions/" + quote(str(id), safe="") + _query(_body(params, kwargs)),
        )
