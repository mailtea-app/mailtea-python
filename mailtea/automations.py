from __future__ import annotations

from typing import Any, Callable, Dict, Optional
from urllib.parse import quote

from ._resource import body as _body, query as _query

RequestFn = Callable[..., Any]


class Automations:
    """The ``automations`` resource (multi-step contact journeys). Access via
    ``mailtea.automations``.

    Automations are scoped to a publication — pass ``publication_id``. An
    automation is a graph: ``steps`` (each ``{"key", "type", "label", "config"}``)
    plus optional ``connections`` (each ``{"from", "to", "branch"}`` — nested
    dicts, so ``"from"`` is written as a plain key, not ``from_``).

    ``connections`` is optional: omit it and the server links the steps in array
    order with ``branch: "next"``, rooted at the trigger. A graph containing a
    ``condition`` or ``wait_for_event`` step cannot be inferred that way and is
    rejected with ``connections_required_for_branching`` — send its connections
    explicitly.

    Failures come back as coded ``issues[]`` rather than schema errors, and for
    a draft/paused/archived automation they ride along informationally instead
    of blocking the save. Every method accepts the payload as a wire-format
    dict, as keyword arguments, or both.
    """

    def __init__(self, request: RequestFn) -> None:
        self._request = request

    def validate(self, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Dry-run a graph without creating anything. Takes ``publication_id``
        and ``steps``, plus optional ``connections``. Returns
        ``{"object": "automation_validation", "valid": ..., "issues": [...]}``."""
        return self._request("POST", "/v1/automations/validate", _body(params, kwargs))

    def create(self, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Create an automation. Takes ``publication_id``, ``name`` and
        ``steps``, plus optional ``description``, ``connections``,
        ``reentry_policy`` (``once``/``once_per_window``/``always`` —
        ``once_per_window`` requires ``reentry_window_seconds``),
        ``on_step_failure``, and ``validate_only``. With ``validate_only=True``
        nothing is written and an ``automation_validation`` is returned instead.
        New automations start as ``draft`` — :meth:`activate` starts them."""
        return self._request("POST", "/v1/automations", _body(params, kwargs))

    def list(self, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """List automations (cursor-paginated). Filters: ``publication_id``
        (required), ``status`` (``draft``/``active``/``paused``/``archived``),
        ``limit``, ``after`` (cursor from a previous ``next_cursor``). List items
        omit ``steps``, ``connections``, ``valid`` and ``issues`` — use
        :meth:`get` for the full graph."""
        return self._request("GET", "/v1/automations" + _query(_body(params, kwargs)))

    def get(self, id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Retrieve one automation with its live graph and current ``issues[]``.
        Requires ``publication_id``."""
        return self._request(
            "GET", "/v1/automations/" + quote(str(id), safe="") + _query(_body(params, kwargs))
        )

    def update(self, id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Update an automation's ``name``, ``description``, ``steps``,
        ``connections``, ``reentry_policy``, ``reentry_window_seconds``, or
        ``on_step_failure``. ``publication_id`` is required (sent as a query
        parameter). The graph is replaced wholesale and cuts a new version.

        ``validate_only=True`` returns an ``automation_validation`` and writes
        nothing. A graph change that carries errors saves anyway while the
        automation is draft/paused/archived; on an ``active`` one it is a 422 —
        pause, save, then start again."""
        merged = _body(params, kwargs)
        publication_id = merged.pop("publication_id", None)
        return self._request(
            "PATCH",
            "/v1/automations/"
            + quote(str(id), safe="")
            + _query({"publication_id": publication_id}),
            merged,
        )

    def delete(self, id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Delete an automation. Requires ``publication_id``. Deleting an
        ``active`` automation is a 409 ``automation_active`` — pause or archive
        it first so its in-flight runs are not dropped silently."""
        return self._request(
            "DELETE", "/v1/automations/" + quote(str(id), safe="") + _query(_body(params, kwargs))
        )

    def activate(self, id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Start the automation so new contacts enroll. Requires
        ``publication_id``. A graph with errors is refused with 422
        ``automation_invalid`` and the blocking ``issues[]``."""
        return self._request(
            "POST",
            "/v1/automations/" + quote(str(id), safe="") + "/activate" + _query(_body(params, kwargs)),
        )

    def pause(self, id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Stop new enrollments. Requires ``publication_id`` (query). Optional
        ``cancel_runs`` — it **defaults to false** here, so in-flight runs keep
        going; pass ``cancel_runs=True`` to exit them. Returns the automation
        plus ``canceled_runs``."""
        return self._lifecycle(id, "/pause", params, kwargs)

    def archive(self, id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Archive the automation. Requires ``publication_id`` (query). Optional
        ``cancel_runs`` — it **defaults to true** here (the opposite of
        :meth:`pause`), so in-flight runs exit with ``automation_archived``.
        Returns the automation plus ``canceled_runs``."""
        return self._lifecycle(id, "/archive", params, kwargs)

    def versions(self, id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """List an automation's versions (cursor-paginated). Filters:
        ``publication_id`` (required), ``limit``, ``after``. List items carry no
        ``steps``/``connections`` — use :meth:`version` for a stored graph."""
        return self._request(
            "GET",
            "/v1/automations/" + quote(str(id), safe="") + "/versions" + _query(_body(params, kwargs)),
        )

    def version(
        self, id: str, version: Any, params: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> Dict[str, Any]:
        """Retrieve one stored version, including its ``steps`` and
        ``connections``. Requires ``publication_id``. This is the graph a run of
        that version is pinned to — editing the automation never rewrites it."""
        return self._request(
            "GET",
            "/v1/automations/"
            + quote(str(id), safe="")
            + "/versions/"
            + quote(str(version), safe="")
            + _query(_body(params, kwargs)),
        )

    def metrics(self, id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Per-step funnel counts for an automation. Filters: ``publication_id``
        (required), ``version`` (omit to aggregate across ALL versions),
        ``since``, ``until`` (ISO 8601). Test runs are always excluded
        (``excludes_test_runs: true``). Condition steps report
        ``branches: {condition_met, condition_not_met}``, ``wait_for_event``
        steps ``{event_received, timeout}``."""
        return self._request(
            "GET",
            "/v1/automations/" + quote(str(id), safe="") + "/metrics" + _query(_body(params, kwargs)),
        )

    def test(self, id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Run the automation once against a real contact. ``publication_id`` is
        required (sent as a query parameter); the body takes one of
        ``contact_id`` or ``email``, plus optional ``event_properties`` to seed
        the run's ``event.*`` namespace.

        A test run **sends real, billed email** to that inbox — it does not
        bypass any send gate. It is flagged ``is_test`` and excluded from
        :meth:`metrics`. Returns 202 with the queued run."""
        merged = _body(params, kwargs)
        publication_id = merged.pop("publication_id", None)
        return self._request(
            "POST",
            "/v1/automations/"
            + quote(str(id), safe="")
            + "/test"
            + _query({"publication_id": publication_id}),
            merged,
        )

    def _lifecycle(
        self, id: str, suffix: str, params: Optional[Dict[str, Any]], kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """``publication_id`` goes in the query but ``cancel_runs`` is read from
        the body, so the two are split here. No body is sent when the caller
        omitted ``cancel_runs`` — or passed it as ``None``, which the server's
        schema would reject — so the per-verb default applies in both cases."""
        merged = _body(params, kwargs)
        cancel_runs = merged.get("cancel_runs")
        body = None if cancel_runs is None else {"cancel_runs": cancel_runs}
        return self._request(
            "POST",
            "/v1/automations/"
            + quote(str(id), safe="")
            + suffix
            + _query({"publication_id": merged.get("publication_id")}),
            body,
        )
