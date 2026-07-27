from __future__ import annotations

from typing import Any, Callable, Dict, Optional
from urllib.parse import quote

from ._resource import body as _body, query as _query

RequestFn = Callable[..., Any]


class AutomationRuns:
    """The ``automation_runs`` resource (one contact's journey through one
    automation). Access via ``mailtea.automation_runs``.

    Runs are nested under an automation and scoped to a publication — pass
    ``automation_id`` and ``publication_id``. A run PINS the automation version
    it started on, so :meth:`get` returns the graph the run is actually
    executing, not the live one. Every method accepts the payload as a
    wire-format dict, as keyword arguments, or both.
    """

    def __init__(self, request: RequestFn) -> None:
        self._request = request

    def list(
        self, automation_id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> Dict[str, Any]:
        """List an automation's runs (cursor-paginated). Filters:
        ``publication_id`` (required), ``status`` (one or more run statuses —
        pass a list and it is joined for you), ``contact_id``, ``is_test``,
        ``limit``, ``after``. List items omit the pinned graph and the step
        runs; use :meth:`get` for those."""
        merged = _body(params, kwargs)
        status = merged.get("status")
        if isinstance(status, (list, tuple)):
            merged["status"] = ",".join(str(item) for item in status)
        # The server matches `is_test` against the literal strings "true"/"false"
        # and 400s on anything else, so Python's `True` cannot go out as-is.
        if isinstance(merged.get("is_test"), bool):
            merged["is_test"] = "true" if merged["is_test"] else "false"
        return self._request(
            "GET",
            "/v1/automations/" + quote(str(automation_id), safe="") + "/runs" + _query(merged),
        )

    def get(
        self,
        automation_id: str,
        run_id: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Retrieve one run in full. Requires ``publication_id``. Returns the
        PINNED ``steps``/``connections``, the per-step ``step_runs``, and
        ``waiting`` (``resume_at`` / ``waiting_event_name``) — read this rather
        than an event ingest's ``resumed_runs`` counter to tell whether an event
        actually advanced the run."""
        return self._request(
            "GET",
            "/v1/automations/"
            + quote(str(automation_id), safe="")
            + "/runs/"
            + quote(str(run_id), safe="")
            + _query(_body(params, kwargs)),
        )

    def cancel(
        self,
        automation_id: str,
        run_id: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Cancel one in-flight run. Requires ``publication_id``. A cancelled
        run cannot be resumed. Returns the run in full detail."""
        return self._request(
            "POST",
            "/v1/automations/"
            + quote(str(automation_id), safe="")
            + "/runs/"
            + quote(str(run_id), safe="")
            + "/cancel"
            + _query(_body(params, kwargs)),
        )
