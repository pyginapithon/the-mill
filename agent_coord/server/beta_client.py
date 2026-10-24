"""Client-lane rules for card 866.

done_when and pass evidence are stored on the card body until the beta
book's card.done_when column and card_event.evidence column are the book.
The cached glance is two result sets from uc_a6_glance_cached.
"""
from __future__ import annotations

from typing import Any

from agent_coord.helpers.errors import CoordError

EVIDENCE_MAX = 2000
DONE_WHEN_MAX = 1000
ACTIVITY_CAP = 30

# The pasted glance row. open_votes is kept when the row has it (beta DDL).
_CACHE_KEYS = (
    "id",
    "at",
    "refresh_us",
    "present",
    "held",
    "open_n",
    "claimed_n",
    "parked_n",
    "shipped_n",
    "done_n",
    "letters_1d",
    "card_moves_1d",
    "doings_1d",
    "holds_1d",
    "points_1d",
)
_ACTIVITY_KEYS = ("seq", "at", "kind", "ref", "desk")
_KINDS = frozenset({"letter", "card", "doing", "hold", "score"})


def evidence_for_pass(step: str, text: Any) -> str | None:
    """Evidence stored on ship or done. --back stores none. Blank stores none."""
    if step == "back":
        return None
    s = "" if text is None else str(text).strip()
    if not s:
        return None
    if len(s) > EVIDENCE_MAX:
        raise CoordError("pass: evidence must be 0..%d chars" % EVIDENCE_MAX)
    return s


def done_when_text(text: Any) -> str | None:
    """Blank clears done_when. A longer line is refused."""
    s = "" if text is None else str(text).strip()
    if not s:
        return None
    if len(s) > DONE_WHEN_MAX:
        raise CoordError("accept: done-when must be 0..%d chars" % DONE_WHEN_MAX)
    return s


def check_accept(status: str, who: str, asker: str, is_admin: bool) -> None:
    """Asker or Admin, and the card is not done. A missing card is 'gone'."""
    if not status or status in ("done", "gone"):
        raise CoordError("accept: card is done or gone")
    if who and who != asker and not is_admin:
        raise CoordError("who-may: done-when is the asker or Admin")


def shape_glance(cache_rows: list[dict] | None, activity_rows: list[dict] | None) -> dict[str, Any]:
    """Two sets. No office-wide unread. Activity is the newest 30."""
    src = cache_rows[0] if cache_rows else {}
    if not isinstance(src, dict):
        src = {}
    cache = {key: src.get(key) for key in _CACHE_KEYS}
    if "open_votes" in src:
        cache["open_votes"] = src.get("open_votes")
    activity: list[dict[str, Any]] = []
    for row in list(activity_rows or [])[:ACTIVITY_CAP]:
        if not isinstance(row, dict):
            continue
        kind = str(row.get("kind") or "")
        if kind not in _KINDS:
            raise CoordError("glance: kind is letter, card, doing, hold or score")
        activity.append({key: row.get(key) for key in _ACTIVITY_KEYS})
    return {"cache": cache, "activity": activity}


def read_cached_glance(cn) -> dict[str, Any]:
    """Call uc_a6_glance_cached and keep its two result sets apart."""
    cur = cn.cursor(dictionary=True)
    sets: list[list[dict]] = []
    try:
        cur.execute("CALL uc_a6_glance_cached()")
        for _ in range(4):
            if getattr(cur, "with_rows", False):
                sets.append(list(cur.fetchall()))
            else:
                sets.append([])
            nxt = getattr(cur, "nextset", None)
            if nxt is None or not nxt():
                break
    except CoordError:
        raise
    except Exception as exc:
        msg = str(exc).lower()
        if "1305" in msg or "does not exist" in msg or "doesn't exist" in msg:
            raise CoordError("glance: the cached glance is not installed") from exc
        raise CoordError("glance: the cached glance could not be read") from exc
    finally:
        try:
            cur.close()
        except Exception:
            pass
    cache = sets[0] if sets else []
    activity = sets[1] if len(sets) > 1 else []
    return shape_glance(cache, activity)
