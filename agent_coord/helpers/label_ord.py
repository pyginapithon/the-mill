"""label.ord: 0 pinned, 65535 unplaced. Gaps stay. Never renumber (#196, #198)."""
from __future__ import annotations

from typing import Any

from agent_coord.helpers.errors import CoordError

ORD_PINNED = 0
ORD_UNPLACED = 65535
ORD_MSG = "ord must be a whole number from 0 to 65535"


def parse_label_ord(value: Any) -> int | None:
    """None keeps the stored ord (a fresh row takes 65535). Otherwise 0..65535."""
    if value is None:
        return None
    if isinstance(value, bool):
        raise CoordError(ORD_MSG)
    if isinstance(value, int):
        n = value
    else:
        text = str(value).strip()
        if text == "":
            return None
        if not text.isdecimal():
            raise CoordError(ORD_MSG)
        n = int(text)
    if n < ORD_PINNED or n > ORD_UNPLACED:
        raise CoordError(ORD_MSG)
    return n


def missing_label(name: str) -> str:
    """Unknown label name. The hint names mill create label (#198)."""
    who = str(name or "").strip()
    return "label: no name %s. mill create label %s" % (who, who)


def unused_label(name: str, first_use_creates: bool) -> str:
    """trail --label on a label nobody has used yet (#709).

    When trust lets first use create it, point to plain first use, not create.
    """
    who = str(name or "").strip()
    if first_use_creates:
        return "label %s has no entries yet; mill label TYPE ID %s tags one (first use creates it)" % (who, who)
    return "label %s has no entries yet; an Admin makes it first: mill create label %s" % (who, who)
