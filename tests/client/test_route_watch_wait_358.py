# -*- coding: utf-8 -*-
"""#358: mill route and mill watch wait for a connect started just before in this shell.

`bash -c 'mill connect DESK & c=$!; trap "kill $c" EXIT; mill route add ...'` used to
fail with "mill connect DESK first" because route read the sitting desk once and never
waited. The RPC verbs (watch rides add) already wait in wait_for_sitting_desk.
"""
from __future__ import annotations

import json

import pytest

from agent_coord import __main__ as cli
from agent_coord.client import tokens
from agent_coord.client import ws as ws_cli


@pytest.fixture(autouse=True)
def _mill_home(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    monkeypatch.setattr(ws_cli, "SITTING_BRIDGE_RETRY_WAIT_S", 0)
    yield


def _starting_then_sitting(monkeypatch, desk: str = "alice") -> dict:
    """Not sitting on the first look; the connect sits on a later look."""
    seen = {"n": 0}

    def bridge(parent_pid=None):
        seen["n"] += 1
        return {"desk": desk} if seen["n"] > 2 else None

    monkeypatch.setattr(tokens, "resolve_desk_owner", lambda cli_owner="", **kw: "")
    monkeypatch.setattr(ws_cli, "bridge_for_parent", bridge)
    monkeypatch.setattr(
        ws_cli,
        "starting_for_parent",
        lambda parent_pid=None: {"desk": desk, "pid": 4, "parent_pid": 1},
    )
    monkeypatch.setattr(ws_cli, "_pid_alive", lambda pid: True)
    monkeypatch.setattr(ws_cli.time, "sleep", lambda s: None)
    return seen


def _last_json(out: str) -> dict:
    at = out.rfind("{\n")
    assert at >= 0, out
    return json.loads(out[at:])


def test_route_add_waits_for_a_starting_connect(monkeypatch, capsys) -> None:
    seen = _starting_then_sitting(monkeypatch)
    rc = cli.main(["route", "add", "todo:TODO", "--", "python", "/abs/on_todo.py"])
    cap = capsys.readouterr()
    assert rc == 0, cap.err
    assert "mill connect DESK first" not in cap.err
    row = _last_json(cap.out)
    assert row["ok"] is True and row["desk"] == "alice" and row["key"] == "todo:TODO"
    assert seen["n"] > 2


def test_route_list_and_rm_wait_too(monkeypatch, capsys) -> None:
    _starting_then_sitting(monkeypatch)
    assert cli.main(["route", "add", "mail:MAIL", "--", "true"]) == 0
    _starting_then_sitting(monkeypatch)
    assert cli.main(["route", "list"]) == 0
    assert "mail:MAIL" in _last_json(capsys.readouterr().out)["routes"][0]
    _starting_then_sitting(monkeypatch)
    assert cli.main(["route", "rm", "mail:MAIL"]) == 0
    assert _last_json(capsys.readouterr().out)["removed"] == "mail:MAIL"


def test_route_without_any_connect_still_fails_closed(monkeypatch, capsys) -> None:
    monkeypatch.setattr(tokens, "resolve_desk_owner", lambda cli_owner="", **kw: "")
    monkeypatch.setattr(ws_cli, "bridge_for_parent", lambda parent_pid=None: None)
    monkeypatch.setattr(ws_cli, "starting_for_parent", lambda parent_pid=None: None)
    monkeypatch.setattr(ws_cli.time, "sleep", lambda s: None)
    assert cli.main(["route", "add", "todo:TODO", "--", "true"]) == 1
    assert "mill connect DESK first" in capsys.readouterr().err


def test_watch_rpc_waits_for_a_starting_connect(monkeypatch) -> None:
    """watch rides the add RPC; the RPC path waits for the sitting desk (guard)."""
    from agent_coord.client import http as http_cli

    _starting_then_sitting(monkeypatch)
    monkeypatch.setattr(http_cli, "resolve_desk_owner", lambda cli_owner="", **kw: "")
    monkeypatch.setattr(http_cli, "mill_url", lambda: "https://wall.example/")
    monkeypatch.setattr(http_cli, "mill_api_key", lambda owner="": "k" if owner == "alice" else "")
    sent: dict = {}

    def fake_call(payload, *, token, desk):
        sent.update(payload=payload, token=token, desk=desk)
        return {"ok": True, "result": {"verb": "add"}}

    monkeypatch.setattr(ws_cli, "mill_ws_call", fake_call)
    out = http_cli.mill_http_call({"verb": "add", "cmd": "add", "owner": "", "type": "todo", "id": 358})
    assert out["ok"] is True
    assert sent["desk"] == "alice" and sent["token"] == "k"
