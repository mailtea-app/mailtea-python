"""Shared helpers for resource classes: payload merging, query strings, and
attribute-access response wrapping."""

from __future__ import annotations

from typing import Any, Dict, Optional
from urllib.parse import urlencode


def body(params: Optional[Dict[str, Any]], kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """Merge a positional wire-format dict with keyword arguments.

    Every method accepts either style (or both — kwargs win on conflict)::

        mailtea.emails.send({"from": "a@b.c", "subject": "Hi"})
        mailtea.emails.send(from_="a@b.c", subject="Hi")

    A single trailing underscore is stripped from kwarg names so Python
    reserved words can be used (``from_`` becomes ``"from"`` on the wire).
    """
    merged = dict(params or {})
    for key, value in kwargs.items():
        merged[key[:-1] if key.endswith("_") else key] = value
    return merged


def query(params: Optional[Dict[str, Any]]) -> str:
    """Render a query string from a dict, dropping ``None`` values."""
    if not params:
        return ""
    clean = {key: value for key, value in params.items() if value is not None}
    return ("?" + urlencode(clean)) if clean else ""


class Resource(dict):
    """An API response: a plain dict that also allows attribute access, so
    both ``email["id"]`` and ``email.id`` work. Nested dicts/lists are wrapped
    on access. Keys that collide with dict methods (``get``, ``items``, …)
    are only reachable via ``[...]`` indexing.
    """

    def __getattr__(self, name: str) -> Any:
        try:
            return wrap(self[name])
        except KeyError:
            raise AttributeError(name) from None


def wrap(value: Any) -> Any:
    if isinstance(value, dict):
        return Resource(value)
    if isinstance(value, list):
        return [wrap(item) for item in value]
    return value
