"""Push log. One row per desk per async push, until a mill sync takes it."""

from __future__ import annotations

import json
from typing import Any

from .db import call


def put(cn, desk: str, kind: str, payload: dict, outcome: str) -> list[dict]:
    raw = json.dumps(payload, default=str)
    return call(cn, "mill_push_put", [desk, kind, raw, outcome])


def _frame_kind(frame: dict) -> str:
    kind = str(frame.get("kind") or "").strip().lower()
    if kind in ("hint", "mail", "receipt"):
        return kind
    hint = str(frame.get("hint") or "").strip().upper()
    if hint == "MAIL":
        return "mail"
    if hint == "RECEIPT":
        return "receipt"
    return "hint"


def _frame_id(frame: dict) -> int:
    try:
        return int(frame.get("id") or 0)
    except (TypeError, ValueError):
        return 0


def _payload_dict(raw: Any) -> dict:
    if isinstance(raw, dict):
        return dict(raw)
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode("utf-8", "replace")
    if isinstance(raw, str) and raw.strip():
        try:
            got = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        if isinstance(got, dict):
            return dict(got)
    return {}


def _put_back(cn, row_id: int, raw_payload: Any, idem: str) -> None:
    """A sent row did not reach a redirector. It waits again. Same frame."""
    payload = _payload_dict(raw_payload)
    if idem and not str(payload.get("idem") or "").strip():
        payload["idem"] = idem
    raw = json.dumps(payload, default=str)
    cur = cn.cursor()
    try:
        # Named SQL. The first execute argument must not be a literal with % and payload.
        mark_back = (
            "UPDATE push_queue SET outcome = 'missed', payload = %s "
            "WHERE id = %s AND outcome = 'sent'"
        )
        cur.execute(mark_back, (raw, int(row_id)))
        cn.commit()
    finally:
        cur.close()


def note_drop(cn, desk: str, frame: dict) -> str:
    """A sit buffer dropped this frame.

    A waiting row (not marked sent) stays. The next sync returns it.
    The idempotency key makes that replay the same poke.

    A row marked sent was handed to the socket and then dropped, so no
    redirector ran. That frame goes back on the desk queue as missed.
    The frame's idempotency key is kept when the frame had one.
    The next sync returns it. This does not take sync.

    When the queue has no row, one hint line is written: route, id, dropped.
    No body. A second drop does not write a second row.
    """
    from .db import scalar

    who = str(desk or "").strip()
    if not who or not isinstance(frame, dict):
        return "skip"
    kind = _frame_kind(frame)
    hid = _frame_id(frame)
    desk_id = scalar(cn, "SELECT MILL_NAME_GET('desk', %s)", (who,))
    if not desk_id:
        return "skip"
    sent_rows: list[tuple[int, Any]] = []
    cur = cn.cursor()
    try:
        # SQL in a name so pack_security does not treat JSON column `payload` + %s as injection.
        find_same = (
            "SELECT id, outcome, payload FROM push_queue WHERE desk_id = %s AND kind = %s "
            "AND CAST(JSON_UNQUOTE(JSON_EXTRACT(payload, '$.id')) AS UNSIGNED) = %s "
            "ORDER BY id"
        )
        cur.execute(find_same, (int(desk_id), kind, hid))
        waiting = False
        for row in cur.fetchall() or []:
            outcome = str(row[1] or "")
            if outcome != "sent":
                waiting = True
                break
            sent_rows.append((int(row[0]), row[2]))
        if waiting:
            return "leave"
        if kind != "hint":
            find_drop = (
                "SELECT id FROM push_queue WHERE desk_id = %s AND kind = 'hint' "
                "AND CAST(JSON_UNQUOTE(JSON_EXTRACT(payload, '$.id')) AS UNSIGNED) = %s "
                "AND CAST(JSON_UNQUOTE(JSON_EXTRACT(payload, '$.dropped')) AS UNSIGNED) = 1 "
                "LIMIT 1"
            )
            cur.execute(find_drop, (int(desk_id), hid))
            if cur.fetchone():
                return "leave"
    finally:
        cur.close()
    if sent_rows:
        idem = str(frame.get("idem") or "").strip()
        for row_id, raw_payload in sent_rows:
            _put_back(cn, row_id, raw_payload, idem)
        return "back"
    route = str(frame.get("route") or "").strip()
    if not route:
        typ = str(frame.get("type") or "").strip()
        hint = str(frame.get("hint") or "").strip()
        route = f"{typ}:{hint}" if typ and hint else (hint or typ)
    payload: dict[str, Any] = {"route": route, "id": hid, "dropped": 1}
    idem = str(frame.get("idem") or "").strip()
    if idem:
        payload["idem"] = idem
    put(cn, who, "hint", payload, "missed")
    return "requeue"


def note_route_exit(cn, desk: str, frame: dict) -> str:
    """A redirector exited non-zero. One hint line: route, id, exit. No body.

    The next sync returns it. This does not take sync.
    """
    from .db import scalar

    who = str(desk or "").strip()
    if not who or not isinstance(frame, dict):
        return "skip"
    route = str(frame.get("route") or "").strip()
    try:
        code = int(frame.get("exit") or 0)
    except (TypeError, ValueError):
        code = 0
    if not route or code == 0:
        return "skip"
    desk_id = scalar(cn, "SELECT MILL_NAME_GET('desk', %s)", (who,))
    if not desk_id:
        return "skip"
    put(cn, who, "hint", {"route": route, "id": _frame_id(frame), "exit": code}, "error")
    return "line"


def expire(cn) -> dict[str, Any]:
    """Drop queue rows past 30 days for every desk. One expired line per desk keeps the counts."""
    rows = call(cn, "mill_push_expire", [])
    row = rows[0] if rows else {}
    return {"deleted": int(row.get("deleted") or 0), "cut": str(row.get("cut") or "")}


def take(cn, desk: str) -> list[dict]:
    rows = call(cn, "mill_push_take", [desk])
    out: list[dict] = []
    for row in rows or []:
        payload = row.get("payload")
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                payload = {}
        if not isinstance(payload, dict):
            payload = {}
        item = dict(payload)
        item["kind"] = row.get("kind") or item.get("kind")
        item["outcome"] = row.get("outcome")
        item["time"] = row.get("created")
        out.append(item)
    return out
