"""Snapshot mill todo (Wall diary) across a schema wipe.

Export writes slugs, not numeric name ids. Restore after sql/ apply:
activity then todo; a missing roster is Office.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from agent_coord.const import CONST_OFFICE, CONST_ROSTER
from agent_coord.client.tokens import mill_home
from agent_coord.helpers.ident import iso6


def backup_dir() -> Path:
    p = mill_home() / "backup"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _name(cn, nid) -> str:
    if not nid:
        return ""
    from agent_coord.server.records.name import by_id

    return by_id(cn, int(nid)) or ""


def export(cn, dest: Path | None = None) -> Path:
    cur = cn.cursor()
    cur.execute(
        "SELECT t.id, t.created, t.updated, t.status, t.body, "
        "un.name AS desk, an.name AS roster, "
        "cn.name AS asker, sn.name AS volunteer "
        "FROM todo t "
        "LEFT JOIN name un ON un.id = t.updated_id "
        "LEFT JOIN name an ON an.id = t.roster_id "
        "LEFT JOIN name cn ON cn.id = t.creator_id "
        "LEFT JOIN name sn ON sn.id = t.assigned_id "
        "ORDER BY t.id"
    )
    cols = list(cur.column_names)
    cards = []
    for tup in cur.fetchall():
        rec = dict(zip(cols, tup))
        cards.append(
            {
                "id": int(rec["id"]),
                "created": iso6(rec["created"]),
                "updated": iso6(rec["updated"]),
                "desk": rec["desk"] or "",
                "group": rec["roster"] or "",
                "asker": rec["asker"] or "",
                "status": rec["status"],
                "volunteer": rec["volunteer"] or "",
                "body": rec["body"] or "",
            }
        )
    cur.execute(
        "SELECT a.type, a.id, a.created, a.updated, a.weight, a.n, "
        "dn.name AS desk, an.name AS roster "
        "FROM activity a "
        "LEFT JOIN name dn ON dn.id = a.desk_id "
        "LEFT JOIN name an ON an.id = a.roster_id "
        "WHERE a.type='todo' ORDER BY a.id"
    )
    pcols = list(cur.column_names)
    pres = []
    for tup in cur.fetchall():
        rec = dict(zip(pcols, tup))
        pres.append(
            {
                "type": rec["type"],
                "id": int(rec["id"]),
                "created": iso6(rec["created"]),
                "updated": iso6(rec["updated"]),
                "desk": rec["desk"] or "",
                "group": rec["roster"] or "",
                "weight": int(rec["weight"] or 1),
                "n": int(rec["n"] or 1),
            }
        )
    atts: list[dict] = []
    cur.close()
    dest = dest or backup_dir() / f"todo-{datetime.now().strftime('%Y-%m-%d')}.json"
    payload = {
        "kind": "mill-todo-diary",
        "exported": iso6(datetime.now()),
        "office_from": "the-mill",
        "todo": cards,
        "activity": pres,
        "attach": atts,
    }
    dest.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return dest


def _nid(cn, slug: str, office_from: str) -> int:
    s = (slug or "").strip()
    if not s:
        raise RuntimeError("todo diary: empty name")
    if s == office_from:
        s = CONST_OFFICE
    from agent_coord.server.records.name import get_or_insert

    return int(get_or_insert(cn, s, CONST_ROSTER))


# Wall keep: parked + in-flight. Dump still has done.
_KEEP = frozenset({"parked", "open", "claimed", "shipped"})


def restore(
    cn, src: Path, *, office_from: str = "the-mill", include_done: bool = False
) -> dict[str, int]:
    data = json.loads(src.read_text(encoding="utf-8"))
    if data.get("kind") != "mill-todo-diary":
        raise RuntimeError("not a mill todo diary dump")
    office_from = str(data.get("office_from") or office_from)
    keep = set(_KEEP)
    if include_done:
        keep.add("done")
    cards = [r for r in (data.get("todo") or []) if (r.get("status") or "open") in keep]
    ids = {int(r["id"]) for r in cards}
    cur = cn.cursor()
    n_pres = 0
    for rec in data.get("activity") or []:
        if int(rec["id"]) not in ids:
            continue
        desk = _nid(cn, rec["desk"], office_from)
        group = _nid(cn, rec["group"], office_from)
        cur.execute(
            "INSERT INTO activity (type, id, created, updated, desk_id, roster_id, weight, n) "
            "VALUES ('todo', %s, %s, %s, %s, %s, %s, %s) "
            "ON DUPLICATE KEY UPDATE updated=VALUES(updated), desk_id=VALUES(desk_id), "
            "roster_id=VALUES(roster_id), weight=VALUES(weight), n=VALUES(n)",
            (
                int(rec["id"]),
                rec.get("created") or None,
                rec.get("updated") or rec.get("created"),
                desk,
                group,
                int(rec.get("weight") or 1),
                int(rec.get("n") or 1),
            ),
        )
        n_pres += 1
    n_todo = 0
    for rec in cards:
        cur.execute(
            "INSERT INTO todo (type, id, created, updated, updated_id, roster_id, creator_id, "
            "status, assigned_id, body) "
            "VALUES ('todo', %s, %s, %s, %s, %s, %s, %s, %s, %s) "
            "ON DUPLICATE KEY UPDATE updated=VALUES(updated), status=VALUES(status), "
            "assigned_id=VALUES(assigned_id), body=VALUES(body)",
            (
                int(rec["id"]),
                rec.get("created") or None,
                rec.get("updated") or rec.get("created"),
                _nid(cn, rec["desk"], office_from),
                _nid(cn, rec["group"], office_from),
                _nid(cn, rec["asker"], office_from),
                rec.get("status") or "open",
                _nid(cn, rec["volunteer"], office_from) if rec.get("volunteer") else None,
                rec.get("body") or "",
            ),
        )
        n_todo += 1
    cn.commit()
    cur.close()
    return {"todo": n_todo, "activity": n_pres, "attach": 0}


def main() -> None:
    import argparse
    import sys

    from agent_coord.server.records.db import connect

    p = argparse.ArgumentParser(description="mill todo diary export/restore")
    p.add_argument("cmd", choices=("export", "restore"))
    p.add_argument("--file", default="")
    p.add_argument(
        "--done",
        action="store_true",
        help="restore done cards too (default: parked/open/claimed/shipped only)",
    )
    args = p.parse_args()
    cn = connect()
    try:
        if args.cmd == "export":
            dest = Path(args.file) if args.file else None
            out = export(cn, dest)
            print(json.dumps({"ok": True, "file": str(out)}, default=str), flush=True)
        else:
            src = Path(args.file) if args.file else backup_dir() / f"todo-{datetime.now().strftime('%Y-%m-%d')}.json"
            if not src.is_file():
                print(f"missing {src}", file=sys.stderr)
                sys.exit(1)
            n = restore(cn, src, include_done=bool(args.done))
            print(json.dumps({"ok": True, "file": str(src), **n}, default=str), flush=True)
    finally:
        cn.close()


if __name__ == "__main__":
    main()
