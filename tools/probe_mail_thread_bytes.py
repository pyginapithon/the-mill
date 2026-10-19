"""Byte probe for mail-thread read scopes (#148) on a seeded fake room.

Seeds a throwaway MySQL schema with a room shaped like agent-ux (a root,
FINDINGS findings replying to it, TRIES replies under each finding, six
desks, ~350-char bodies) and prints the CLI-sized JSON bytes of:

  classic   mail-thread <room> --room      (the pre-#148 default, whole room)
  summary   mail-thread <room>             (new default for a room name)
  branch    mail-thread <finding id>       (new default for a mail id)
  subtree   mail-thread <finding id> --subtree
  after     mail-thread <room> --after <id> (catch-up, last TRIES letters)

and a day-one task (find the room, read one finding and its tries) under the
classic read versus the new defaults. Drops the schema afterwards.

Run: AGENT_COORD_HOST=... AGENT_COORD_PORT=... python tools/probe_mail_thread_bytes.py
"""
from __future__ import annotations

import json
import os
import sys

# Run against this checkout, not whatever the venv has installed.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

FINDINGS = int(os.environ.get("PROBE_FINDINGS", "12"))
TRIES = int(os.environ.get("PROBE_TRIES", "3"))
BODY = int(os.environ.get("PROBE_BODY", "350"))
DESKS = ["pdesk1", "pdesk2", "pdesk3", "pdesk4", "pdesk5", "pdesk6"]


class _Book:
    def __init__(self, cn):
        self._cn = cn


def _body(tag: str) -> str:
    line = f"{tag}: verb: mail-thread error: example text minute: 14:52 PT desk: tester mill: 0.6.27. "
    return (line * (BODY // len(line) + 1))[:BODY]


def _bytes(result: dict) -> int:
    # Same shape the CLI prints: {"id", "ok", "result"} as compact JSON.
    env = {"id": "00000000-0000-0000-0000-000000000000", "ok": True, "result": result}
    return len(json.dumps(env, default=str).encode("utf-8"))


def main() -> int:
    import mysql.connector

    from agent_coord.server.api.mill import rpc
    from agent_coord.server.records import apply, connect
    from agent_coord.server.records import name as rec_name
    from agent_coord.server.records.db import conn_kwargs

    db = f"mill_probe_mt_{os.getpid()}"
    kw = conn_kwargs()
    kw.pop("database", None)
    kw["autocommit"] = True
    admin = mysql.connector.connect(**kw)
    cur = admin.cursor()
    cur.execute(f"CREATE DATABASE `{db}` DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_0900_ai_ci")
    os.environ["AGENT_COORD_DATABASE"] = db
    try:
        cn = connect(db)
        apply(cn, wipe=True)
        rec_name.get_or_insert(cn, "the-mill", "roster")
        for d in DESKS:
            rec_name.get_or_insert(cn, d, "desk")
        book = _Book(cn)
        owner = DESKS[0]
        root = int(
            rpc._h_send(
                book,
                {"src": owner, "dst": ",".join(DESKS[1:]), "body": _body("root"), "name": "probe-ux"},
                "the-mill",
                owner,
            )["id"]
        )
        findings: list[int] = []
        for i in range(FINDINGS):
            who = DESKS[(i % (len(DESKS) - 1)) + 1]
            fid = int(rpc._h_reply(book, {"mail_id": root, "body": _body(f"finding {i}")}, "the-mill", who)["id"])
            findings.append(fid)
            for j in range(TRIES):
                w2 = DESKS[(i + j) % len(DESKS)]
                rpc._h_reply(book, {"mail_id": fid, "body": _body(f"try {i}.{j}")}, "the-mill", w2)
        target = findings[len(findings) // 2]
        reader = DESKS[4]

        def read(**b):
            return rpc._h_mail_thread(book, b, "the-mill", reader)

        classic = read(tree="probe-ux", scope="room")
        summary = read(tree="probe-ux")
        branch = read(mail_id=target)
        subtree = read(mail_id=target, scope="subtree")
        ids = [int(m["id"]) for m in classic["chain"]]
        after = read(tree="probe-ux", after=ids[-(TRIES + 1)])
        rows = {
            "classic (--room)": classic,
            "summary (room name)": summary,
            "branch (mail id)": branch,
            "subtree (--subtree)": subtree,
            "after (--after)": after,
        }
        print(f"room: {len(ids)} letters ({FINDINGS} findings x {TRIES} tries + root), body {BODY} chars")
        for k, v in rows.items():
            print(f"  {k:22s} {len(v['chain']):3d} letters {_bytes(v):7d} bytes")
        day_classic = _bytes(classic) * 2  # find the room, then re-read it to answer
        day_new = _bytes(summary) + _bytes(subtree)  # summary, then the finding's subtree
        print(f"day-one read (find room + read one finding with its tries):")
        print(f"  classic: 2 x --room            {day_classic:7d} bytes")
        print(f"  new:     summary + --subtree   {day_new:7d} bytes")
        print(f"  saved:   {100 - (100 * day_new // max(day_classic, 1))}%")
        cn.close()
    finally:
        cur.execute(f"DROP DATABASE IF EXISTS `{db}`")
        cur.close()
        admin.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
