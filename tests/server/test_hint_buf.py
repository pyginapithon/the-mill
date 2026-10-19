# -*- coding: utf-8 -*-
from agent_coord.server.hint_buf import HintBuf


def test_ping_not_queued(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("agent_coord.config.mill_home", lambda: tmp_path)
    buf = HintBuf("alice", maxsize=8)
    buf.put_recv({"type": "heartbeat", "id": 0, "hint": "PING"})
    assert buf.get_work(timeout=0.05) is None


def test_mail_queued_fifo(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("agent_coord.config.mill_home", lambda: tmp_path)
    buf = HintBuf("alice", maxsize=8)
    buf.put_recv({"type": "mail", "id": 1, "hint": "MAIL"})
    buf.put_recv({"type": "todo", "id": 2, "hint": "TODO"})
    a = buf.get_work(timeout=0.2)
    b = buf.get_work(timeout=0.2)
    assert a and a["hint"] == "MAIL" and a["id"] == 1
    assert b and b["hint"] == "TODO" and b["id"] == 2


def test_full_keeps_the_dropped_frame_for_the_office(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("agent_coord.config.mill_home", lambda: tmp_path)
    buf = HintBuf("alice", maxsize=2)
    buf.put_recv({"type": "todo", "id": 1, "hint": "TODO", "idem": "hint:todo:1:alice"})
    buf.put_recv({"type": "todo", "id": 2, "hint": "TODO"})
    buf.put_recv({"type": "hold", "id": 3, "hint": "HOLD"})
    dropped = buf.pop_drops()
    assert len(dropped) == 1
    assert dropped[0]["id"] == 1
    assert dropped[0]["route"] == "todo:TODO"
    assert buf.pop_drops() == []
    a = buf.get_work(timeout=0.2)
    b = buf.get_work(timeout=0.2)
    assert a and a["id"] == 2
    assert b and b["id"] == 3


def test_full_drops_oldest(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("agent_coord.config.mill_home", lambda: tmp_path)
    buf = HintBuf("alice", maxsize=2)
    buf.put_recv({"hint": "MAIL", "id": 1})
    buf.put_recv({"hint": "TODO", "id": 2})
    buf.put_recv({"hint": "HOLD", "id": 3})
    a = buf.get_work(timeout=0.2)
    b = buf.get_work(timeout=0.2)
    assert a and a["id"] == 2
    assert b and b["id"] == 3
    assert buf.get_work(timeout=0.05) is None


def test_two_desks_do_not_share_queue_or_file(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("agent_coord.config.mill_home", lambda: tmp_path)
    alice = HintBuf("alice", maxsize=8)
    bob = HintBuf("bob", maxsize=8)
    alice.put_recv({"hint": "MAIL", "id": 11})
    bob.put_recv({"hint": "TODO", "id": 22})
    a = alice.get_work(timeout=0.2)
    b = bob.get_work(timeout=0.2)
    assert a and a["id"] == 11 and a["desk"] == "alice"
    assert b and b["id"] == 22 and b["desk"] == "bob"
    assert alice.path != bob.path
    assert alice.path.name == "alice.hints.jsonl"
    assert bob.path.name == "bob.hints.jsonl"
    assert alice.get_work(timeout=0.05) is None
    assert bob.get_work(timeout=0.05) is None
