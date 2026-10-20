"""Refuse silent cuts on hold resource and watcher hint (#143). The note bound is the stored body (#360)."""
from __future__ import annotations

from agent_coord.helpers.errors import CoordError

HINT_MAX = 4096
RESOURCE_MAX = 64


def resource_name(raw: str) -> str:
    text = "" if raw is None else str(raw)
    if len(text) < 1 or len(text) > RESOURCE_MAX:
        raise CoordError(f"resource must be 1..{RESOURCE_MAX} characters")
    return text


def bound_watcher_hint(hint: str) -> str:
    text = "" if hint is None else str(hint)
    if len(text) > HINT_MAX:
        raise CoordError(
            f"watcher: hint would be {len(text)} chars (max {HINT_MAX}); shorten"
        )
    return text
