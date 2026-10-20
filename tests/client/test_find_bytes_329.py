"""The bytes field matches the reply as printed, after --find and grouping (#329)."""
from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from agent_coord.client import http


def _card(i, need, detail):
    return {"project_id": "cold-test", "need_id": need, "id": i, "status": "open",
            "detail": detail, "volunteer": "", "asker": "a", "tree": None, "labels": []}


BOARD = [_card(i, f"hard1-{'a' if i < 3 else 'z'}-{i}", "x" * 5000) for i in range(40)]


@pytest.fixture
def wall(monkeypatch):
    from agent_coord.server.mill_json import with_bytes

    def fake(body):
        reply, _ = with_bytes({"id": "r1", "ok": True, "result": list(BOARD), "sync": [], "mill": "t"})
        return reply

    monkeypatch.setattr(http, "_todo_call", lambda args, body: fake(body))
    monkeypatch.setattr("agent_coord.client.outbound.body_from_args", lambda args: {"verb": "todo"})


def _run(capsys, **kw):
    base = dict(cmd="todo", project="cold-test", need="", find="", group_by="", raw=False, said_verb="")
    base.update(kw)
    assert http.mill_http_from_args(SimpleNamespace(**base)) == 0
    line = capsys.readouterr().out.strip().splitlines()[-1]
    return line, json.loads(line)


def test_find_reports_the_printed_size(wall, capsys):
    line, row = _run(capsys, find="hard1-a-")
    assert len(row["result"]) == 3
    assert row["bytes"] == len(line.encode("utf-8"))
    assert row["wire_bytes"] > 100_000  # the whole board still crossed the wire


def test_grouped_board_reports_the_printed_size(wall, capsys):
    line, row = _run(capsys)
    assert row["bytes"] == len(line.encode("utf-8"))


def test_reply_without_bytes_gets_none(monkeypatch, capsys):
    monkeypatch.setattr(http, "_todo_call", lambda args, body: {"ok": True, "result": []})
    monkeypatch.setattr("agent_coord.client.outbound.body_from_args", lambda args: {"verb": "todo"})
    _line, row = _run(capsys)
    assert "bytes" not in row


def test_unchanged_reply_has_no_wire_bytes(monkeypatch, capsys):
    from agent_coord.server.mill_json import with_bytes

    reply, n = with_bytes({"id": "r2", "ok": True, "result": {"ok": True}, "sync": [], "mill": "t"})
    monkeypatch.setattr(http, "_todo_call", lambda args, body: dict(reply))
    monkeypatch.setattr("agent_coord.client.outbound.body_from_args", lambda args: {"verb": "pass"})
    line, row = _run(capsys, cmd="pass")
    assert row["bytes"] == n == len(line.encode("utf-8"))
    assert "wire_bytes" not in row
