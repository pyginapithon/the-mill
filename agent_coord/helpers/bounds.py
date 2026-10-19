"""Refuse silent cuts on note detail, hold resource, and watcher hint (#143)."""
from __future__ import annotations

from agent_coord.helpers.errors import CoordError

NOTE_MAX = 4096
HINT_MAX = 4096
RESOURCE_MAX = 64


def resource_name(raw: str) -> str:
    text = "" if raw is None else str(raw)
    if len(text) < 1 or len(text) > RESOURCE_MAX:
        raise CoordError(f"resource must be 1..{RESOURCE_MAX} characters")
    return text


def append_note_detail(prev: str, note: str, *, replace: bool) -> str:
    base = "" if replace or not str(prev or "").strip() else str(prev)
    extra = "" if note is None else str(note)
    joined = extra if not base else base + "\n" + extra
    if len(joined) > NOTE_MAX:
        raise CoordError(
            f"note: detail would be {len(joined)} chars (max {NOTE_MAX}); use --replace or shorten"
        )
    return joined


def bound_watcher_hint(hint: str) -> str:
    text = "" if hint is None else str(hint)
    if len(text) > HINT_MAX:
        raise CoordError(
            f"watcher: hint would be {len(text)} chars (max {HINT_MAX}); shorten"
        )
    return text
