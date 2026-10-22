"""#671 a sync hands over one item per hinted object, not every change of it.
grok-bot's first wake replayed 61 HOLD hints for one hold (2026-10-06 to
10-19, all missed) on its sync line. A hint is a poke about an object (the
same poke key every time), so the sync folds a desk's hint rows for one
(type, id, outcome) into the latest one, with n (how many) and first (the
oldest time). Letters, receipts, route exit and drop lines stay one each.
Row F-sync-hint-fold."""
from __future__ import annotations

import json

from agent_coord.server.records import push as rec_push


def _row(n, kind, payload, outcome="missed", t=None):
    return {"id": n, "kind": kind, "payload": json.dumps(payload), "outcome": outcome,
            "created": t or f"2026-10-{6 + n % 20:02d} 07:00:{n % 60:02d}"}


def _take(monkeypatch, rows):
    monkeypatch.setattr(rec_push, "call", lambda cn, proc, args: rows)
    return rec_push.take(object(), "grok-bot")


def test_a_hold_backlog_is_one_item_with_its_count(monkeypatch):
    rows = [_row(i, "hint", {"type": "hold", "id": 78, "hint": "HOLD", "detail": {"when": i}}) for i in range(61)]
    rows.insert(30, _row(100, "hint", {"type": "todo", "id": 72, "hint": "TODO"}))
    got = _take(monkeypatch, rows)
    assert [(i["type"], i["id"]) for i in got] == [("todo", 72), ("hold", 78)]
    hold = got[1]
    assert hold["n"] == 61
    assert hold["detail"] == {"when": 60}  # the latest change
    assert hold["first"] == rows[0]["created"] and hold["time"] == rows[-1]["created"]
    assert "n" not in got[0]  # a single hint is unchanged


def test_letters_receipts_and_report_lines_stay_one_each(monkeypatch):
    rows = [
        _row(1, "mail", {"id": 9}), _row(2, "mail", {"id": 9}),
        _row(3, "receipt", {"id": 9}), _row(4, "receipt", {"id": 9}),
        _row(5, "hint", {"route": "todo:TODO", "id": 7, "exit": 3}, "error"),
        _row(6, "hint", {"route": "todo:TODO", "id": 7, "exit": 3}, "error"),
        _row(7, "hint", {"route": "hold:HOLD", "id": 8, "dropped": 1}),
        _row(8, "hint", {"route": "hold:HOLD", "id": 8, "dropped": 1}),
    ]
    got = _take(monkeypatch, rows)
    assert len(got) == 8 and not any("n" in i for i in got)


def test_sent_and_missed_rows_of_one_hint_stay_apart(monkeypatch):
    """A sent row was walked live; a missed row is still to walk. Never merged."""
    rows = [
        _row(1, "hint", {"type": "hold", "id": 78, "hint": "HOLD"}, "sent"),
        _row(2, "hint", {"type": "hold", "id": 78, "hint": "HOLD"}, "missed"),
        _row(3, "hint", {"type": "hold", "id": 78, "hint": "HOLD"}, "missed"),
    ]
    got = _take(monkeypatch, rows)
    assert [(i["outcome"], i.get("n")) for i in got] == [("sent", None), ("missed", 2)]
