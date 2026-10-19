# -*- coding: utf-8 -*-
"""A non-zero redirector writes one sync line. No body."""
from agent_coord.server.records import push as rec_push


def test_note_route_exit_writes_route_id_and_code(monkeypatch) -> None:
    stored: list[tuple] = []
    monkeypatch.setattr("agent_coord.server.records.db.scalar", lambda cn, sql, args: 7)
    monkeypatch.setattr(
        rec_push,
        "put",
        lambda cn, desk, kind, payload, outcome: stored.append((desk, kind, payload, outcome)),
    )
    assert rec_push.note_route_exit(
        object(),
        "grok-tui",
        {"route": "todo:TODO", "id": 4, "exit": 3, "detail": "nope"},
    ) == "line"
    assert stored == [("grok-tui", "hint", {"route": "todo:TODO", "id": 4, "exit": 3}, "error")]


def test_note_route_exit_skips_a_zero_code(monkeypatch) -> None:
    monkeypatch.setattr(
        rec_push,
        "put",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("put")),
    )
    assert rec_push.note_route_exit(object(), "grok-tui", {"route": "todo:TODO", "id": 4, "exit": 0}) == "skip"
