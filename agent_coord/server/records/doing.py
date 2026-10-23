"""#818 PR B: doing entries written by `--doing` on an activity command, and
the reads behind `mill connected` (what each desk is doing, and its history).

Writes: one entry per command, linked to the item that command wrote. The
newest entry is the desk's current doing. There is no end step: the entry
ends on its own when the desk replies under the letter, passes the card (or
the card is done), or drops the hold (see mill_doing_end).
"""

from __future__ import annotations

from typing import Any

from agent_coord.const import CONST_DESK

from .db import call

TEXT_MAX = 512
ON_TYPES = ("mail", "todo", "hold", "score")


def put(cn, desk: str, text: str, on_type: str, on_id: int) -> dict[str, Any]:
    from agent_coord.server.records.name import bare

    rows = call(cn, "mill_doing_put", [bare(desk, CONST_DESK), text[:TEXT_MAX], on_type, int(on_id)])
    return rows[0] if rows else {}


def now(cn, desk: str = "", roster: str = "", all_desks: bool = False) -> list[dict[str, Any]]:
    from agent_coord.server.records.name import bare

    return call(
        cn,
        "mill_doing_now",
        [bare(desk, CONST_DESK) if desk else "", roster or "", 1 if all_desks else 0],
    ) or []


def history(cn, desk: str = "", since: str | None = None, page: int = 1, size: int = 50) -> list[dict[str, Any]]:
    from agent_coord.server.records.name import bare

    return call(
        cn,
        "mill_doing_history",
        [bare(desk, CONST_DESK) if desk else "", since, int(page), int(size)],
    ) or []
