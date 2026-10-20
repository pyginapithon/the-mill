"""Desk focus: the label whose name is the desk id ranks that desk's cards (#374).

Anyone ranks a card for a desk with `mill label todo <id> <desk> --ord N`
(0 pinned, 65535 unplaced). Two readers, both on existing read paths:

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
    """(todo id, ord) wearing label desk, in the wall's rank order. [] on any failure."""
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
    return out


def order_mine(cards: list, desk: str, rank: list[tuple[int, int]]) -> tuple[list, int, int]:
    """Focus cards (label desk) in rank order, then cards desk volunteered for.

    Only cards already on the board are listed, so the board's status and done
    filters hold. A focus card the label read did not return keeps board order
    after the ranked ones with ord UNPLACED. Returns (cards, focus n, claimed n).
    """
    where = {cid: (k, o) for k, (cid, o) in enumerate(rank)}
    focus: list[tuple[int, int, dict]] = []
    claimed: list[dict] = []
    for i, r in enumerate(cards):
        if not isinstance(r, dict):
            continue
        labels = r.get("labels") if isinstance(r.get("labels"), list) else []
        if desk in labels:
            k, o = where.get(r.get("id"), (len(rank) + i, UNPLACED))
            focus.append((k, i, dict(r, focus=o)))
        elif str(r.get("volunteer") or "") == desk:
            claimed.append(r)
    focus.sort(key=lambda t: (t[0], t[1]))
    return [c for _, _, c in focus] + claimed, len(focus), len(claimed)


def wears(cards: list, desk: str) -> bool:
    return any(isinstance(r, dict) and desk in (r.get("labels") or []) for r in cards)


def connect_block(call: Callable[[dict], Any], desk: str) -> dict | None:
    """The focus line connect prints once seated, or None when there is nothing to show."""
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
        if card is None or str(card.get("status") or "") == "done":
            continue
        cards.append(dict({k: card.get(k, "") for k in CARD_KEYS}, rank=ord_))
    if not cards:
        return None
    return {"kind": "focus", "label": desk, "cards": cards, "rest": REST}
