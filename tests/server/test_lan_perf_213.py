"""Fixture check only. lane_stall is not product code (#213).

The 22:18-22:22 PT lane stall is lock wait between two desks, not one hot query.
Fixture lines are the shape from mill-perf.log (PDT window 2026-10-11T05:18Z).
A slow procedure followed by a same-second burst of ~2ms calls is a wait, then a release.
This file does not import the server.
"""
from __future__ import annotations


FIXTURE = """
2026-10-11T05:18:12Z op=sql.mill_tree_select ms=576.8 n=7 ok=1
2026-10-11T05:18:30Z op=verb ms=19506.7 desk=cold-ab-d2 verb=reply ok=1
2026-10-11T05:18:32Z op=sql.mill_mail_get ms=3.2 n=2 ok=1
2026-10-11T05:18:32Z op=sql.mill_tree_select ms=2.1 n=15 ok=1
2026-10-11T05:18:32Z op=sql.mill_member_select ms=2.0 n=1 ok=1
2026-10-11T05:19:59Z op=verb ms=20314.0 desk=cold-ab-c2 verb=mail-thread ok=1
""".strip()


def _rows(text: str) -> list[dict]:
    out = []
    for line in text.splitlines():
        if " op=" not in line:
            continue
        stamp, rest = line.split(" ", 1)
        kv = {}
        op = ""
        for part in rest.split():
            if part.startswith("op="):
                op = part[3:]
            elif "=" in part:
                k, v = part.split("=", 1)
                kv[k] = v
        kv["op"] = op
        kv["stamp"] = stamp
        kv["ms"] = float(kv.get("ms") or 0)
        out.append(kv)
    return out


def lane_stall(rows: list[dict]) -> str:
    """Name the shape of this fixture. Not a server helper."""
    commands = [r for r in rows if r["op"] == "verb" and r["ms"] >= 5000]
    desks = {r.get("desk") for r in commands if r.get("desk")}
    slow_sql = [r for r in rows if str(r["op"]).startswith("sql.") and r["ms"] >= 500]
    by_sec: dict[str, int] = {}
    for row in rows:
        if str(row["op"]).startswith("sql.") and row["ms"] < 20:
            by_sec[row["stamp"][:19]] = by_sec.get(row["stamp"][:19], 0) + 1
    if len(desks) >= 2 and slow_sql and any(n >= 2 for n in by_sec.values()):
        return "wait"
    return "query"


def test_two_desk_burst_is_a_wait():
    assert lane_stall(_rows(FIXTURE)) == "wait"


def test_one_slow_query_without_a_burst_is_not_a_wait():
    rows = _rows("2026-10-11T05:18:01Z op=sql.mill_tree_select ms=900 n=7 ok=1")
    assert lane_stall(rows) == "query"
