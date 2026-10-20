"""Desk focus: the label whose name is the desk id ranks that desk's cards (#374).

Anyone ranks a card for a desk with `mill label todo <id> <desk> --ord N`
(0 pinned, 65535 unplaced). Two readers, both on existing read paths:

Focus skips cards that are done, parked, or held by another desk. Rank is
ord ascending (0 pinned first), ties by card id. Client only: the wall
serves the same reads it did in 0.7.8, so an older client sees nothing new.

- `todo --mine` lists the focus cards on the board first, in label rank
  order (one `trail --label <desk>` read, only when a board card wears it),
  then the desk's claimed cards.
- `mill connect`, once seated, prints one `{"kind": "focus"}` line with the
  top FOCUS_TOP not-done focus cards, so the desk knows what to work on next
  without asking; nothing when there are none.
"""
from __future__ import annotations

from typing import Any, Callable

FOCUS_TOP = 5
FOCUS_PEEKS = 10  # card reads connect spends looking for FOCUS_TOP not-done ones
UNPLACED = 65535
# What a desk needs to act on a card: which one, where (claim takes roster and need),
# its state, who has it, and its rank on the label.
CARD_KEYS = ("id", "project_id", "need_id", "status", "volunteer")
REST = "mill todo --mine lists every focus card, then your claimed ones"


def set_focus_hint(desk: str) -> str:
    return f"rank a card first with mill label todo <id> {desk} --ord 0"


def _result(reply: Any) -> Any:
    if not isinstance(reply, dict) or reply.get("ok") is not True:
        return None
    return reply.get("result")


def label_rank(call: Callable[[dict], Any], desk: str) -> list[tuple[int, int]]:
    """(todo id, ord) wearing label desk, ord ascending (0 pinned first), ties by card id.

    [] on any failure.
    """
    try:
        res = _result(call({"verb": "trail", "label": desk}))
    except Exception:
        return []
    rows = res.get("rows") if isinstance(res, dict) else None
    out: list[tuple[int, int]] = []
    for r in rows if isinstance(rows, list) else []:
        if isinstance(r, dict) and r.get("type") == "todo":
            try:
                out.append((int(r["id"]), int(r.get("ord") or 0)))
            except (KeyError, TypeError, ValueError):
                continue
    out.sort(key=lambda t: (t[1], t[0]))
    return out


def actionable(card: dict, desk: str, status_asked: str = "") -> bool:
    """A focus card the desk can work on: not done, not parked (unless --status
    parked was asked), and not held by another desk (volunteer empty or desk)."""
    st = str(card.get("status") or "")
    if st == "done" and status_asked != "done":
        return False
    if st == "parked" and status_asked != "parked":
        return False
    return str(card.get("volunteer") or "") in ("", desk)


def order_mine(
    cards: list, desk: str, rank: list[tuple[int, int]], status_asked: str = ""
) -> tuple[list, int, int]:
    """Focus cards (label desk, actionable) by rank, then cards desk volunteered for.

    Rank is ord ascending, ties by card id; a focus card the label read did not
    return counts as ord UNPLACED. A card is listed once: a focus card the desk
    already holds sits in the focus part. Only cards already on the board are
    listed, so the board's status and done filters hold.
    Returns (cards, focus n, claimed n).
    """
    ords = {cid: o for cid, o in rank}
    focus: list[tuple[int, int, dict]] = []
    claimed: list[dict] = []
    for r in cards:
        if not isinstance(r, dict):
            continue
        labels = r.get("labels") if isinstance(r.get("labels"), list) else []
        mine = str(r.get("volunteer") or "") == desk
        if desk in labels and actionable(r, desk, status_asked):
            o = ords.get(r.get("id"), UNPLACED)
            focus.append((o, int(r.get("id") or 0), dict(r, focus=o)))
        elif mine:
            claimed.append(r)
    focus.sort(key=lambda t: (t[0], t[1]))
    return [c for _, _, c in focus] + claimed, len(focus), len(claimed)


def wears(cards: list, desk: str) -> bool:
    return any(isinstance(r, dict) and desk in (r.get("labels") or []) for r in cards)


def connect_block(call: Callable[[dict], Any], desk: str) -> dict | None:
    """The focus line connect prints once seated, or None when there is nothing to show.

    The top FOCUS_TOP actionable focus cards (see actionable) in rank order.
    """
    rank = label_rank(call, desk)
    cards: list[dict] = []
    for cid, ord_ in rank[:FOCUS_PEEKS]:
        if len(cards) >= FOCUS_TOP:
            break
        try:
            res = _result(call({"verb": "todo", "project": "", "need": str(cid)}))
        except Exception:
            continue
        card = res[0] if isinstance(res, list) and res and isinstance(res[0], dict) else None
        if card is None or not actionable(card, desk):
            continue
        cards.append(dict({k: card.get(k, "") for k in CARD_KEYS}, rank=ord_))
    if not cards:
        return None
    return {"kind": "focus", "label": desk, "cards": cards, "rest": REST}
