"""CALL mill_watcher_* - who to poke after an activity write."""
from __future__ import annotations

from agent_coord.const import CONST_MAIL
from agent_coord.helpers.errors import CoordError

from .db import call

NOT_ON_MAIL = "watchers do not watch mail; mail has recipients: mill add mail:ID WHO"


def _watchable(type: str) -> None:
    """mail is not a watcher kind (#270): refuse plainly before the ENUM does."""
    if str(type or "").strip().lower() == CONST_MAIL:
        raise CoordError(NOT_ON_MAIL)


def put(cn, type: str, id: int, desk_id: int) -> list[dict]:
    _watchable(type)
    return call(cn, "mill_watcher_put", [type, id, desk_id])


def select(cn, type: str, id: int) -> list[dict]:
    return call(cn, "mill_watcher_select", [type, id])


def delete(cn, type: str, id: int, desk_id: int) -> list[dict]:
    _watchable(type)
    return call(cn, "mill_watcher_delete", [type, id, desk_id])


def set_hint(cn, type: str, id: int, desk_id: int, hint: str | None) -> list[dict]:
    """Put this desk as watcher and set per-listener hint recipe (NULL/empty clears)."""
    _watchable(type)
    return call(cn, "mill_watcher_set_hint", [type, id, desk_id, hint or ""])


def glance_rows(cn, roster_ids: list[int] | None = None) -> list[dict]:
    """Who watches what, for the Wall. Hint text and endpoints stay off this list."""
    if roster_ids is not None and not roster_ids:
        return []
    cur = cn.cursor()
    try:
        sql = (
            "SELECT w.type, w.id, n.name AS desk, n.type AS desk_type,"
            " (w.hint IS NOT NULL AND w.hint <> '') AS custom,"
            " a.roster_id, s.kpi AS kpi"
            " FROM watcher w"
            " JOIN name n ON n.id = w.desk_id"
            " LEFT JOIN activity a ON a.type = w.type AND a.id = w.id"
            " LEFT JOIN score s ON w.type = 'score' AND s.id = w.id"
        )
        args: list[int] = []
        if roster_ids:
            marks = ",".join(["%s"] * len(roster_ids))
            sql += f" WHERE a.roster_id IN ({marks})"
            args = list(roster_ids)
        sql += " ORDER BY w.type, w.id, n.name"
        cur.execute(sql, args)
        cols = list(cur.column_names)
        return [dict(zip(cols, r)) for r in cur.fetchall()]
    finally:
        cur.close()


def pack_watchers(rows: list[dict] | None) -> list[dict]:
    """Floor watchers. hint is only 'custom' or 'default'."""
    out: list[dict] = []
    for raw in rows or []:
        custom = raw.get("custom")
        flag = "custom" if str(custom).strip() in {"1", "True", "true"} or custom is True else "default"
        out.append(
            {
                "type": str(raw.get("type") or ""),
                "id": int(raw.get("id") or 0),
                "desk": str(raw.get("desk") or ""),
                "roster_id": str(raw.get("roster_id") or ""),
                "title": str(raw.get("title") or ""),
                "status": str(raw.get("status") or ""),
                "hint": flag,
            }
        )
    return out


def group_watchers(rows: list[dict] | None) -> list[dict]:
    """One floor row per activity. Types match watcher.type in tables.sql."""
    groups: dict[tuple, dict] = {}
    order: list[tuple] = []
    for row in rows or []:
        typ = str(row.get("type") or "")
        key = (typ, int(row.get("id") or 0))
        if key not in groups:
            groups[key] = {
                "type": typ,
                "id": key[1],
                "roster_id": str(row.get("roster_id") or ""),
                "title": str(row.get("title") or ""),
                "status": str(row.get("status") or ""),
                "desks": [],
            }
            order.append(key)
        groups[key]["desks"].append(
            {"desk": str(row.get("desk") or ""), "hint": str(row.get("hint") or "default")}
        )
    return [groups[k] for k in order]
