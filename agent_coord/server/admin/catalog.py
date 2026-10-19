"""Name catalog. Mint is any seated desk when trust is high, Admin when limited.

Reclaim, rename, and retire are always Admin. Name twice + yes.
Office and Admin never retire.
"""
from __future__ import annotations

from typing import Any

from agent_coord.const import CONST_ROSTER

from agent_coord.helpers.errors import CoordError
from agent_coord.server.records import name as rec_name
from agent_coord.server.admin.guard import require_admin, require_admin_if_limited


def _stored(value: Any) -> str:
    return str(value or "").strip()


def _live_kind(cn, name: str) -> str:
    """Type of one live name row. A bare string shared by two types returns one row."""
    from agent_coord.server.records.db import scalar

    rec = scalar(
        cn,
        "SELECT type FROM name WHERE name=%s AND deleted IS NULL",
        (name.strip(),),
    )
    if rec is None:
        raise CoordError(f"name {name.strip()!r} is not in the name table")
    if isinstance(rec, (bytes, bytearray)):
        rec = rec.decode("utf-8")
    return str(rec)


def _yes(body: dict[str, Any]) -> None:
    if not body.get("yes"):
        raise CoordError("Admin catalog: name twice + --yes")


def _match(a: str, b: str, *, verb: str) -> None:
    if a != b:
        raise CoordError(f"name mismatch: mill {verb} NAME NAME --yes")


def put_roster(cn, desk: str, body: dict[str, Any]) -> list[dict]:
    """0.7.0: one roster type replaces group (project) and role."""
    require_admin_if_limited(cn, desk)
    _yes(body)
    a = _stored(body.get("slug"))
    b = _stored(body.get("confirm"))
    _match(a, b, verb="roster")
    return rec_name.host_put(cn, a, CONST_ROSTER)


def put_label_name(cn, desk: str, body: dict[str, Any]) -> list[dict]:
    require_admin_if_limited(cn, desk)
    _yes(body)
    a = _stored(body.get("slug"))
    b = _stored(body.get("confirm"))
    _match(a, b, verb="label")
    return rec_name.host_put(cn, a, "label")


def reclaim(cn, desk: str, body: dict[str, Any]) -> list[dict]:
    require_admin(cn, desk)
    _yes(body)
    a = str(body.get("slug") or "").strip()
    b = str(body.get("confirm") or "").strip()
    _match(a, b, verb="reclaim")
    return rec_name.reclaim(cn, a, _live_kind(cn, a))


def rename(cn, desk: str, body: dict[str, Any]) -> list[dict]:
    require_admin(cn, desk)
    _yes(body)
    old = str(body.get("old") or "").strip()
    new = str(body.get("new") or "").strip()
    confirm = str(body.get("confirm") or "").strip()
    _match(new, confirm, verb="rename")
    return rec_name.rename(cn, old, new, _live_kind(cn, old))


def retire(cn, desk: str, body: dict[str, Any]) -> list[dict]:
    require_admin(cn, desk)
    _yes(body)
    a = str(body.get("slug") or "").strip()
    b = str(body.get("confirm") or "").strip()
    _match(a, b, verb="retire")
    return rec_name.retire(cn, a, _live_kind(cn, a))
