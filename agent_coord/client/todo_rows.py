"""Short rows and paging for the todo board list (client side, #295).

Default: each card prints as a short row (id, need, status, volunteer), at
most TODO_PAGE cards per reply, and a page block says where you are.
When every card on the page sits on one roster, project_id moves to the page
block once instead of repeating on each row. --page N reads page N.
--full prints today's reply: every card and every field, no paging. A NEED
peek, --find and --raw keep their own shapes and are never cut or paged.
"""
from __future__ import annotations

from typing import Any

from agent_coord.helpers.errors import CoordError

TODO_PAGE = 50
SHORT_KEYS = ("id", "need_id", "status", "volunteer", "project_id")
FULL_HINT = "short rows; --full prints every field of every card"


def applies(args: Any, find: str) -> bool:
    """True when this todo call lists the board in short rows."""
    if str(getattr(args, "cmd", "") or "") != "todo" or bool(getattr(args, "full", False)):
        return False
    page = int(getattr(args, "page", 0) or 0)
    other = (
        "a NEED peek is one card" if str(getattr(args, "need", "") or "")
        else "--find already lists only the matches" if find
        else "--raw prints every card" if bool(getattr(args, "raw", False))
        else ""
    )
    if other:
        if page:
            raise CoordError(f"todo --page: {other}; drop --page")
        return False
    return True


def cut(rows: list, page: int) -> tuple[list, dict]:
    """The cards on page (1-based; 0 = first) and the page block."""
    n = max(1, page)
    of = max(1, -(-len(rows) // TODO_PAGE))
    if n > of:
        raise CoordError(f"todo --page {n}: {len(rows)} card(s) make {of} page(s)")
    part = rows[(n - 1) * TODO_PAGE : n * TODO_PAGE]
    block: dict[str, Any] = {"n": n, "of": of, "size": TODO_PAGE, "cards": len(rows)}
    rosters = {r.get("project_id") for r in part if isinstance(r, dict)}
    if len(rosters) == 1 and None not in rosters:
        block["roster"] = rosters.pop()
    if n < of:
        block["next"] = f"--page {n + 1}"
    block["full"] = FULL_HINT
    return part, block


def short(result: Any, roster: str = "") -> Any:
    """Short rows in a flat or grouped todo result; groups and order stay."""
    keys = tuple(k for k in SHORT_KEYS if not (roster and k == "project_id"))

    def one(r: Any) -> Any:
        return {k: r[k] for k in keys if k in r} if isinstance(r, dict) else r

    if isinstance(result, list):
        return [one(r) for r in result]
    if isinstance(result, dict) and isinstance(result.get("groups"), list):
        out = dict(result)
        out["groups"] = [dict(g, items=[one(r) for r in g.get("items") or []]) for g in result["groups"]]
        return out
    return result
