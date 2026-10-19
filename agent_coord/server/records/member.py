"""member - N-N desk on a roster (unordered, members equal). Self only. Office never leave."""

from __future__ import annotations

from agent_coord.const import CONST_OFFICE, CONST_ROSTER

from .db import call


def _slot(cn, group: str, kind: str = "") -> tuple[str, str]:
    """Stored roster name plus its name type (always roster)."""
    from agent_coord.server.records.name import pair

    _k, stored = pair(group, CONST_ROSTER)
    return stored, CONST_ROSTER


def put(cn, group: str, desk: str, kind: str = "") -> list[dict]:
    from agent_coord.server.records import name as rec_name

    slot, k = _slot(cn, group, kind)
    rec_name.ensure_roster(cn, slot, k)
    return call(cn, "mill_member_put", [k, slot, (desk or "").strip()])


def delete(cn, group: str, desk: str, kind: str = "") -> list[dict]:
    slot, k = _slot(cn, group, kind)
    return call(cn, "mill_member_delete", [k, slot, (desk or "").strip()])


def select(cn, group: str = "", desk: str = "", kind: str = "") -> list[dict]:
    if group:
        slot, k = _slot(cn, group, kind)
    else:
        slot, k = "", kind or ""
    d = (desk or "").strip()
    return call(cn, "mill_member_select", [k, slot, d])


def put_office(cn, desk: str) -> list[dict]:
    return put(cn, CONST_OFFICE, desk)
