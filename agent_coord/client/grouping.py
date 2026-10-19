"""List output grouping for todo, inbox and hold --peek (client side, 0.7.x).

Default: each list in its native structure - todos by plan tree, mail by room
tree, holds flat. --group-by tree|label|roster overrides it. The wall sorts
rows stably (plan, then id); grouping keeps that order inside each group.

What each list can group by (#274):
  todo:  tree (plan), label, roster.
  inbox: tree (room), roster (sender roster). No label until mail labels exist.
  hold:  label, roster. Holds sit on no tree.
A --group-by outside that table can never apply and is refused (exit 2).
A row with no value lists under "(none)". A row with several labels lists
under each of them. A default view where no row has a plan or room stays flat.
"""
from __future__ import annotations

from typing import Any, Callable

NATIVE = {"todo": "tree", "inbox": "tree", "hold": ""}
BY = ("tree", "label", "roster")
CAN = {
    "todo": ("tree", "label", "roster"),
    "inbox": ("tree", "roster"),
    "hold": ("label", "roster"),
}
NONE = "(none)"


def refusal(cmd: str, by: str) -> str:
    """One line when --group-by BY can never apply to CMD; empty when it can."""
    if not by or cmd not in CAN or by in CAN[cmd]:
        return ""
    can = "|".join(CAN[cmd])
    why = {
        ("inbox", "label"): "mail has no labels yet",
        ("hold", "tree"): "holds sit on no tree",
    }.get((cmd, by), f"{cmd} rows carry no {by}")
    return f"{cmd} --group-by {by}: {why}; use --group-by {can}"


def _keys_fn(cmd: str, by: str) -> Callable[[dict], list[str]] | None:
    def one(v: Any) -> list[str]:
        return [str(v)] if v not in (None, "") else []

    if by == "tree":
        return lambda r: one(r.get("tree"))
    if by == "roster":
        if cmd == "inbox":
            return lambda r: one((r.get("sender") or {}).get("roster"))
        if cmd == "todo":
            return lambda r: one(r.get("project_id"))
        return lambda r: one(r.get("roster"))
    if by == "label":
        return lambda r: [str(x) for x in (r.get("labels") or []) if x not in (None, "")]
    return None


def group_rows(rows: list[dict], keys: Callable[[dict], list[str]], by: str) -> dict:
    groups: dict[str, list[dict]] = {}
    for r in rows:
        for k in keys(r) or [NONE]:
            groups.setdefault(k, []).append(r)
    # Named groups first, in first-seen order (the wall's stable sort); "(none)" last.
    if NONE in groups:
        groups[NONE] = groups.pop(NONE)
    return {"group_by": by, "groups": [{"key": k, "items": v} for k, v in groups.items()]}


def apply(cmd: str, result: Any, by: str = "") -> tuple[Any, str]:
    """Return (result, note). The note is always empty; refusals happen up front (refusal())."""
    asked = bool(by)
    by = by or NATIVE.get(cmd, "")
    if not by or refusal(cmd, by):
        return result, ""
    holder = None
    rows = result
    if cmd == "hold" and isinstance(result, dict) and isinstance(result.get("holds"), list):
        holder, rows = result, result["holds"]
    if not isinstance(rows, list) or not all(isinstance(r, dict) for r in rows):
        return result, ""
    fn = _keys_fn(cmd, by)
    if fn is None or not rows:
        return result, ""
    if not asked and not any(fn(r) for r in rows):
        # Default view and no row on a plan or room: stay a flat list, no note.
        return result, ""
    grouped = group_rows(rows, fn, by)
    if holder is not None:
        out = dict(holder)
        out.pop("holds", None)
        out.update(grouped)
        return out, ""
    return grouped, ""
