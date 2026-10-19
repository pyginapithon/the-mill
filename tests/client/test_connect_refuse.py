# -*- coding: utf-8 -*-
"""Card #332: client side of mill connect -r/--refuse. Regression row F43 (connect-refuse)."""
from __future__ import annotations

import asyncio
import json
import threading
from types import SimpleNamespace

import pytest

from agent_coord.__main__ import _build_parser
from agent_coord.client import ws as ws_cli


class _Rcvd:
    def __init__(self, code: int, reason: str = "") -> None:
        self.code = code
        self.reason = reason


class ConnectionClosedError(Exception):
    def __init__(self, code: int, reason: str = "") -> None:
        super().__init__(f"received {code} ({reason})")
        self.rcvd = _Rcvd(code, reason)


class FakeWS:
    def __init__(self, fail: BaseException) -> None:
        self.fail = fail

    async def send(self, text: str) -> None:
        pass

    async def recv(self) -> str:
        raise self.fail


REASON = "seat in use: alice since 2026-10-19T23:00:00Z"


@pytest.fixture(autouse=True)
def _mill_home(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    # _sit_session prints the ready line once per desk per process; keep that set local.
    monkeypatch.setattr(ws_cli, "_READY_DESKS", set())
    yield


@pytest.mark.parametrize("verb", ["connect", "connect-wait"])
def test_refuse_flag_parses(verb: str) -> None:
    p = _build_parser()
    assert p.parse_args([verb, "alice", "-r"]).refuse is True
    assert p.parse_args([verb, "alice", "--refuse"]).refuse is True
    assert p.parse_args([verb, "alice"]).refuse is False


def test_refuse_adds_query_param() -> None:
    url = "wss://wall.example.com/ws/alice"
    assert ws_cli.refuse_url(url, False) == url
    assert ws_cli.refuse_url(url, True) == url + "?refuse=1"


def test_in_use_close_is_terminal_with_distinct_exit(capsys) -> None:
    stop = threading.Event()
    outcome: dict = {}

    async def reopen():
        raise AssertionError("a refused connect must not reconnect")

    async def go() -> None:
        fake = FakeWS(ConnectionClosedError(ws_cli.WS_IN_USE_CLOSE, REASON))
        await ws_cli._sit_session(fake, "alice", stop, None, reconnect=reopen, outcome=outcome)

    asyncio.run(go())
    assert outcome["exit"] == 6
    assert len({4, 5, outcome["exit"]}) == 3
    line = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert line["ok"] is False
    assert "seat in use" in line["error"]
    assert "since 2026-10-19T23:00:00Z" in line["error"]
    # Names the command that does take the seat.
    assert "mill connect alice" in line["error"]
    assert "without -r" in line["error"]
    assert ws_cli.reconnect_stopped(ws_cli.WS_IN_USE_CLOSE, {}) is True


def test_connect_wait_refused_returns_in_use_with_exit(monkeypatch) -> None:
    def _run(coro):
        coro.close()
        raise ConnectionClosedError(ws_cli.WS_IN_USE_CLOSE, REASON)

    monkeypatch.setattr(asyncio, "run", _run)
    got = ws_cli.wait_one_hint("alice", "seat", refuse=True)
    assert got["ok"] is False
    assert got["exit"] == 6
    assert "seat in use" in got["error"]
    assert "mill connect alice" in got["error"]


def test_connect_wait_exits_with_the_in_use_code(monkeypatch, capsys) -> None:
    from agent_coord.client.http import mill_here_over_http

    monkeypatch.setattr("agent_coord.client.tokens.read_session_token", lambda owner, **k: "seat")
    seen: dict = {}

    def _wait(desk, token, **kw):
        seen.update(kw)
        return {"ok": False, "error": "seat in use", "desk": desk, "exit": 6}

    monkeypatch.setattr("agent_coord.client.ws.wait_one_hint", _wait)
    args = SimpleNamespace(cmd="connect", desk="alice", project="", vendor="", session="",
                           foreground=True, refuse=True)
    assert mill_here_over_http(args) == 6
    assert seen["refuse"] is True


def test_plain_connect_passes_refuse_to_the_socket(monkeypatch) -> None:
    from agent_coord.client import http as http_cli

    monkeypatch.setattr("agent_coord.client.tokens.read_session_token", lambda owner, **k: "seat")
    seen: dict = {}

    def _start(who, tok, stop, outcome, refuse=False):
        seen["refuse"] = refuse
        outcome["exit"] = 6
        stop.set()

    monkeypatch.setattr("agent_coord.client.ws.start_ws_thread", _start)
    monkeypatch.setattr(http_cli, "check_project_on_socket", lambda *a, **k: None)
    monkeypatch.setattr("agent_coord.client.ws.hold_sync_lines", lambda: None)
    args = SimpleNamespace(cmd="connect", desk="alice", project="Office", vendor="", session="",
                           foreground=False, refuse=True)
    assert http_cli.mill_here_over_http(args) == 6
    assert seen["refuse"] is True
