# -*- coding: utf-8 -*-
"""mill connect reconnects after a recoverable close and keeps the bridge (#133)."""
from __future__ import annotations

import asyncio
import json
import threading

import pytest

from agent_coord.client import ws as ws_cli


class _Rcvd:
    def __init__(self, code: int) -> None:
        self.code = code


class _Closed(Exception):
    def __init__(self, code: int) -> None:
        super().__init__(f"received {code} (test)")
        self.rcvd = _Rcvd(code)


class FakeWS:
    def __init__(self, fail: BaseException | None = None) -> None:
        self.sent: list[str] = []
        self.fail = fail
        self._q: asyncio.Queue[str] | None = None

    async def send(self, text: str) -> None:
        self.sent.append(text)

    async def recv(self) -> str:
        if self.fail is not None:
            raise self.fail
        assert self._q is not None
        return await self._q.get()


@pytest.fixture(autouse=True)
def _mill_home(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    monkeypatch.setattr(ws_cli, "SITTING_BRIDGE_RETRY_WAIT_S", 0)
    yield


def test_close_code_and_backoff() -> None:
    assert ws_cli.close_code_of(None) is None
    assert ws_cli.close_code_of(_Closed(1012)) == 1012
    assert ws_cli.close_code_of(RuntimeError("received 1011 (internal)")) == 1011
    assert ws_cli.close_code_of(RuntimeError("connection reset")) is None
    assert ws_cli.reconnect_delay_s(0, jitter=0.0) == 1.0
    assert ws_cli.reconnect_delay_s(1, jitter=0.0) == 2.0
    assert ws_cli.reconnect_delay_s(2, jitter=0.0) == 4.0
    assert ws_cli.reconnect_delay_s(10, jitter=0.0) == 60.0
    assert ws_cli.reconnect_delay_s(0, jitter=0.2) == pytest.approx(1.2)
    assert ws_cli.retry_notice_seconds(1.2) == 1
    assert ws_cli.retry_notice_seconds(60.0) == 60


def test_recoverable_close_keeps_bridge_and_retries(capsys) -> None:
    stop = threading.Event()
    calls: list[int] = []

    async def reopen():
        assert ws_cli.read_rpc_bridge("DESK_alice") is not None
        calls.append(1)
        stop.set()
        fresh = FakeWS()
        fresh._q = asyncio.Queue()
        return fresh

    async def go() -> None:
        fake = FakeWS(fail=_Closed(1012))
        fake._q = asyncio.Queue()
        await ws_cli._sit_session(fake, "DESK_alice", stop, None, reconnect=reopen)

    asyncio.run(go())
    err = capsys.readouterr().err
    assert calls == [1]
    assert "server restarting, retrying in " in err
    assert err.strip().endswith("s")
    assert ws_cli.read_rpc_bridge("DESK_alice") is None


def test_terminal_close_does_not_reconnect(capsys) -> None:
    stop = threading.Event()
    calls: list[int] = []

    async def reopen():
        calls.append(1)
        return FakeWS()

    async def go() -> None:
        fake = FakeWS(fail=_Closed(4401))
        await ws_cli._sit_session(fake, "DESK_alice", stop, None, reconnect=reopen)

    asyncio.run(go())
    err = capsys.readouterr().err
    assert calls == []
    assert "server restarting" not in err
    assert ws_cli.read_rpc_bridge("DESK_alice") is None


def test_terminal_close_sets_distinct_exit(capsys) -> None:
    """4401 and 4000 print a clear error and distinct non-zero exits (#136)."""

    async def _one(code: int) -> dict:
        stop = threading.Event()
        outcome: dict = {}

        async def reopen():
            raise AssertionError("terminal close must not reconnect")

        fake = FakeWS(fail=_Closed(code))
        await ws_cli._sit_session(
            fake, "DESK_alice", stop, None, reconnect=reopen, outcome=outcome
        )
        return outcome

    out_4401 = asyncio.run(_one(4401))
    out_4000 = asyncio.run(_one(4000))
    text = capsys.readouterr().out
    assert out_4401["exit"] == 4
    assert out_4000["exit"] == 5
    assert out_4401["exit"] != out_4000["exit"]
    assert "token rejected (4401): mill join again" in text
    assert "superseded (4000): another connect took this seat" in text


def test_reconnect_stopped_names_the_terminal_exits() -> None:
    assert ws_cli._RECONNECT_CAP_S == 60.0
    assert ws_cli.reconnect_stopped(1012, None) is False
    blank: dict = {}
    assert ws_cli.reconnect_stopped(4401, blank) is True
    assert blank["exit"] == 4
    gone: dict = {}
    assert ws_cli.reconnect_stopped(4000, gone) is True
    assert gone["exit"] == 5
    assert ws_cli.reconnect_stopped(None, {"exit": 4}) is True
    assert ws_cli.reconnect_stopped(None, {}) is False


def test_outer_loop_stops_after_a_terminal_sit(monkeypatch) -> None:
    import asyncio

    stop = threading.Event()
    outcome: dict = {}
    calls = {"n": 0}

    def fake_run(coro):
        calls["n"] += 1
        coro.close()
        if calls["n"] > 1:
            stop.set()
            return None
        outcome["exit"] = 4
        return None

    monkeypatch.setattr(asyncio, "run", fake_run)
    ws_cli.run_ws_loop("alice", "", stop, outcome=outcome)
    assert calls["n"] == 1
    assert stop.is_set()


def test_outer_loop_stops_on_a_terminal_handshake(monkeypatch) -> None:
    import asyncio

    stop = threading.Event()
    outcome: dict = {}
    calls = {"n": 0}

    def fake_run(coro):
        calls["n"] += 1
        coro.close()
        if calls["n"] > 1:
            stop.set()
            return None
        raise _Closed(4401)

    monkeypatch.setattr(asyncio, "run", fake_run)
    ws_cli.run_ws_loop("alice", "", stop, outcome=outcome)
    assert calls["n"] == 1
    assert outcome["exit"] == 4
    assert stop.is_set()


def test_outer_loop_still_retries_a_restart(monkeypatch) -> None:
    import asyncio

    stop = threading.Event()
    calls = {"n": 0}

    def fake_run(coro):
        calls["n"] += 1
        coro.close()
        if calls["n"] >= 2:
            stop.set()
            return None
        raise _Closed(1012)

    monkeypatch.setattr(asyncio, "run", fake_run)
    monkeypatch.setattr(ws_cli, "reconnect_delay_s", lambda attempt, jitter=None: 0.0)
    ws_cli.run_ws_loop("alice", "", stop, outcome={})
    assert calls["n"] == 2


def test_superseded_close_does_not_reconnect() -> None:
    stop = threading.Event()
    calls: list[int] = []

    async def reopen():
        calls.append(1)
        return FakeWS()

    async def go() -> None:
        fake = FakeWS(fail=_Closed(4000))
        await ws_cli._sit_session(fake, "DESK_alice", stop, None, reconnect=reopen)

    asyncio.run(go())
    assert calls == []
