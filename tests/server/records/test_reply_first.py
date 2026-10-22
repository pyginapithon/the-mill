"""F24: one-statement CALL returns callproc's rows; the command score is parked, then batched."""
from __future__ import annotations

import pytest

from agent_coord.server import score_system as ss
from agent_coord.server.records import db


@pytest.mark.sql
@pytest.mark.parametrize(
    "name,args",
    [
        ("mill_hold_select", [""]),
        ("mill_join_select", [""]),
        ("mill_todo_select", ["Office", ""]),
        ("mill_score_select", ["Office"]),
        ("mill_name_select_none", None),
    ],
)
def test_one_statement_call_matches_callproc(cn, name, args):
    if args is None:
        with pytest.raises(Exception):
            db.call(cn, name, [])
        return
    cur = cn.cursor()
    try:
        cur.callproc(name, list(args))
        legacy = db.drain_proc(cur)
    finally:
        db.finish_cursor(cur)
        cur.close()
    cn.commit()
    assert db.call(cn, name, args) == legacy
    assert not cn.in_transaction


def test_odd_proc_name_keeps_callproc():
    seen = {}

    class Cur:
        def callproc(self, name, args):
            seen["callproc"] = (name, args)

        def execute(self, *a, **k):  # pragma: no cover - must not run
            raise AssertionError("execute")

        def stored_results(self):
            return []

        def fetchall(self):
            return []

    assert db._run_proc(Cur(), "bad name; DROP", [1]) == []
    assert seen["callproc"] == ("bad name; DROP", [1])


def test_enqueue_parks_and_flush_writes_one_connection(monkeypatch):
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.setattr(ss, "_ensure_flusher", lambda: None)
    ss._command_q.clear()
    writes = []
    opened = []

    class Cn:
        def close(self):
            opened.append("closed")

    monkeypatch.setattr(db, "connect", lambda *a, **k: opened.append("open") or Cn())
    monkeypatch.setattr(ss, "note_command", lambda d, v, **k: writes.append((d, v, k["req_b"], k["resp_b"], k["ms"], type(k["cn"]).__name__)))
    ss.enqueue_command("desk-a", "todo", req_b=3, resp_b=9, ms=4.5)
    ss.enqueue_command("desk-b", "send", req_b=1, resp_b=2, ms=1.0)
    assert writes == [] and len(ss._command_q) == 2
    assert ss.flush_commands() == 2
    assert writes == [("desk-a", "todo", 3, 9, 4.5, "Cn"), ("desk-b", "send", 1, 2, 1.0, "Cn")]
    assert opened == ["open", "closed"] and ss._command_q == []
    assert ss.flush_commands() == 0 and opened == ["open", "closed"]


def test_queue_is_capped(monkeypatch):
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.setattr(ss, "_ensure_flusher", lambda: None)
    monkeypatch.setattr(ss, "_COMMAND_Q_MAX", 3)
    ss._command_q.clear()
    for i in range(5):
        ss.enqueue_command("d", "v%d" % i)
    assert [v for _d, v, *_ in ss._command_q] == ["v2", "v3", "v4"]
    ss._command_q.clear()


def test_flush_survives_a_down_book(monkeypatch):
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.setattr(ss, "_ensure_flusher", lambda: None)
    ss._command_q.clear()
    ss.enqueue_command("d", "todo")

    def down(*a, **k):
        raise RuntimeError("book down")

    monkeypatch.setattr(db, "connect", down)
    assert ss.flush_commands() == 0 and ss._command_q == []


def test_under_pytest_the_write_is_inline(monkeypatch):
    got = []
    monkeypatch.setattr(ss, "note_command", lambda d, v, **k: got.append((d, v)))
    ss.enqueue_command("d", "todo")
    assert got == [("d", "todo")] and ss._command_q == []
