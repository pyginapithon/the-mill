# -*- coding: utf-8 -*-
"""Localhost RPC bridge: mill_ws_call uses sitting mill connect, not a second /ws."""
from __future__ import annotations

import asyncio
import json
import os
import sys
import threading
from typing import Any

import pytest

from agent_coord.client.session_errors import SESSION_WS_BRIDGE_REQUIRED
from agent_coord.helpers.errors import CoordError
from agent_coord.client import ws as ws_cli


@pytest.fixture(autouse=True)
def _mill_home(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    # Fail-closed tests must not pay the #121 ready-wait; race tests set it explicitly.
    monkeypatch.setattr(ws_cli, "SITTING_BRIDGE_RETRY_WAIT_S", 0)
    yield


def test_mill_ws_call_requires_sitting_bridge() -> None:
    with pytest.raises(CoordError) as ei:
        ws_cli.mill_ws_call(
            {"verb": "inbox", "project": "the-mill"},
            token="tok",
            desk="DESK_alice",
        )
    assert str(ei.value) == SESSION_WS_BRIDGE_REQUIRED
    assert "connect" in str(ei.value).lower()



def test_a_sit_session_one_socket_rpc_and_hint() -> None:
    """Sitting /ws multiplex: HINT to buf; RPC on same FakeWS (no second socket)."""

    class FakeWS:
        def __init__(self) -> None:
            self.sent: list[str] = []
            self._q: asyncio.Queue[str] | None = None

        async def send(self, text: str) -> None:
            self.sent.append(text)
            req = json.loads(text)
            assert self._q is not None
            self._q.put_nowait(
                json.dumps({"id": req["id"], "ok": True, "result": {"via": "ws", "n": 2}})
            )

        async def recv(self) -> str:
            assert self._q is not None
            return await self._q.get()

    stop = threading.Event()
    fake = FakeWS()
    from agent_coord.server.hint_buf import HintBuf

    buf = HintBuf("DESK_alice", maxsize=8)

    async def go() -> Any:
        fake._q = asyncio.Queue()
        sit = asyncio.create_task(ws_cli._sit_session(fake, "DESK_alice", stop, buf))
        ep = None
        for _ in range(100):
            ep = ws_cli.read_rpc_bridge("DESK_alice")
            if ep:
                break
            await asyncio.sleep(0.02)
        assert ep
        fake._q.put_nowait(json.dumps({"type": "mail", "id": 9, "hint": "MAIL"}))
        await asyncio.sleep(0.05)
        reader, writer = await asyncio.open_connection("127.0.0.1", int(ep["port"]))
        req = {
            "id": "r1",
            "verb": "inbox",
            "args": {"project": "the-mill"},
            "secret": ep["secret"],
        }
        writer.write((json.dumps(req) + "\n").encode("utf-8"))
        await writer.drain()
        line = await asyncio.wait_for(reader.readline(), timeout=5.0)
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass
        stop.set()
        sit.cancel()
        try:
            await sit
        except asyncio.CancelledError:
            pass
        return json.loads(line.decode("utf-8"))

    reply = asyncio.run(go())
    assert reply == {"id": "r1", "ok": True, "result": {"via": "ws", "n": 2}}
    assert len(fake.sent) == 1
    wire = json.loads(fake.sent[0])
    assert wire["verb"] == "inbox"
    assert "secret" not in wire
    got = buf.get_work(timeout=0.5)
    assert got is not None
    assert got.get("hint") == "MAIL"


def test_b_mill_ws_call_uses_bridge_not_websockets(monkeypatch) -> None:
    """Command hits localhost bridge; websockets.connect must not run (no second /ws)."""
    secret = "bridge-secret"
    ws_cli.write_rpc_bridge("DESK_alice", port=12345, secret=secret, pid=os.getpid())
    hits = {"ws": 0, "conn": 0}

    class _Sock:
        def __init__(self) -> None:
            self._buf = b""
            self._replies: list[bytes] = []

        def settimeout(self, t: float) -> None:
            return None

        def sendall(self, data: bytes) -> None:
            req = json.loads(data.split(b"\n", 1)[0].decode("utf-8"))
            assert req["secret"] == secret
            assert req["verb"] == "inbox"
            reply = {"id": req["id"], "ok": True, "result": [{"id": 11}]}
            self._replies.append((json.dumps(reply) + "\n").encode("utf-8"))

        def recv(self, n: int) -> bytes:
            if not self._replies:
                return b""
            return self._replies.pop(0)

        def close(self) -> None:
            return None

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake_connect(addr, timeout=None):
        hits["conn"] += 1
        assert addr[0] == "127.0.0.1"
        assert addr[1] == 12345
        return _Sock()

    def boom(*a, **k):
        hits["ws"] += 1
        raise AssertionError("must not open a second /ws")

    monkeypatch.setattr(ws_cli.socket, "create_connection", fake_connect)
    monkeypatch.setattr("websockets.connect", boom, raising=False)
    out = ws_cli.mill_ws_call(
        {"verb": "inbox", "project": "the-mill"},
        token="unused",
        desk="DESK_alice",
    )
    assert out["ok"] is True
    assert out["result"] == [{"id": 11}]
    assert out["sync"] == []
    assert hits["conn"] == 1
    assert hits["ws"] == 0


def test_c_mill_ws_call_reads_bridge_endpoint(monkeypatch, tmp_path) -> None:
    """mill_ws_call refuses when bridge file port is unreachable (no silent /ws fallback)."""
    ws_cli.write_rpc_bridge("DESK_alice", port=1, secret="x", pid=os.getpid())

    def boom(*a, **k):
        raise AssertionError("must not open a second /ws")

    monkeypatch.setattr("websockets.connect", boom, raising=False)
    with pytest.raises(CoordError) as ei:
        ws_cli.mill_ws_call({"verb": "inbox"}, token="t", desk="DESK_alice")
    assert str(ei.value) == SESSION_WS_BRIDGE_REQUIRED


def test_stale_bridge_pid_cleared(tmp_path) -> None:
    path = ws_cli.write_rpc_bridge("DESK_bob", port=59999, secret="x", pid=1)
    path.write_text(
        json.dumps(
            {"desk": "DESK_bob", "host": "127.0.0.1", "port": 59999, "secret": "x", "pid": -1}
        )
        + "\n",
        encoding="utf-8",
    )
    assert ws_cli.read_rpc_bridge("DESK_bob") is None


def test_pid_alive_nonpositive() -> None:
    assert ws_cli._pid_alive(0) is False
    assert ws_cli._pid_alive(-1) is False


def test_pid_alive_current_process() -> None:
    """Live PID must stay alive - Windows os.kill(pid,0) WinError 87 used to lie."""
    assert ws_cli._pid_alive(os.getpid()) is True


def test_live_bridge_pid_kept(tmp_path) -> None:
    """Sitting connect must not delete ws.rpc for its own live pid (Windows regression)."""
    path = ws_cli.write_rpc_bridge("DESK_alice", port=4242, secret="s", pid=os.getpid())
    assert path.is_file()
    ep = ws_cli.read_rpc_bridge("DESK_alice")
    assert ep is not None
    assert ep["pid"] == os.getpid()
    assert ep["port"] == 4242
    assert path.is_file()


@pytest.mark.skipif(sys.platform != "win32", reason="win32 proc_token path only")
def test_pid_alive_win32_uses_proc_token(monkeypatch) -> None:
    import agent_coord.lib.proc as proc

    calls: list[int] = []

    def fake_token(pid: int):
        calls.append(int(pid))
        return 1  # non-None => alive

    monkeypatch.setattr(proc, "proc_token", fake_token)
    assert ws_cli._pid_alive(12345) is True
    assert calls == [12345]

    monkeypatch.setattr(proc, "proc_token", lambda pid: None)
    assert ws_cli._pid_alive(99999) is False


def test_sitting_miss_retries_once_then_succeeds(monkeypatch) -> None:
    """#121 GO A: first bridge miss, short wait, second hit succeeds."""
    secret = "bridge-secret"
    sleeps: list[float] = []
    lookups = {"n": 0}

    real_bridge = ws_cli.bridge_for_parent

    def flaky_bridge(parent_pid=None):
        lookups["n"] += 1
        if lookups["n"] == 1:
            return None
        ws_cli.write_rpc_bridge("DESK_alice", port=12345, secret=secret, pid=os.getpid())
        return real_bridge(parent_pid)

    class _Sock:
        def __init__(self) -> None:
            self._replies: list[bytes] = []

        def settimeout(self, t: float) -> None:
            return None

        def sendall(self, data: bytes) -> None:
            req = json.loads(data.split(b"\n", 1)[0].decode("utf-8"))
            reply = {"id": req["id"], "ok": True, "result": [{"id": 1}], "sync": []}
            self._replies.append((json.dumps(reply) + "\n").encode("utf-8"))

        def recv(self, n: int) -> bytes:
            if not self._replies:
                return b""
            return self._replies.pop(0)

        def close(self) -> None:
            return None

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(ws_cli, "bridge_for_parent", flaky_bridge)
    monkeypatch.setattr(ws_cli, "SITTING_BRIDGE_RETRY_WAIT_S", 0.5)
    monkeypatch.setattr(ws_cli.time, "sleep", lambda s: sleeps.append(float(s)))
    monkeypatch.setattr(ws_cli.socket, "create_connection", lambda *a, **k: _Sock())

    out = ws_cli.mill_ws_call({"verb": "inbox", "project": "the-mill"}, token="t", desk="DESK_alice")
    assert out["ok"] is True
    assert out["result"] == [{"id": 1}]
    assert lookups["n"] == 2
    assert sleeps == [0.5]


def test_starting_connect_is_polled_until_the_bridge_exists(monkeypatch) -> None:
    """#210: a live starting connect is polled. A missing connect is not."""
    sleeps: list[float] = []
    lookups = {"n": 0}

    def bridge(parent_pid=None):
        lookups["n"] += 1
        if lookups["n"] < 3:
            return None
        return {
            "host": "127.0.0.1",
            "port": 9,
            "secret": "s",
            "pid": 1,
            "parent_pid": 1,
            "desk": "alice",
        }

    class _Sock:
        def __init__(self) -> None:
            self._replies: list[bytes] = []

        def settimeout(self, t: float) -> None:
            return None

        def sendall(self, data: bytes) -> None:
            req = json.loads(data.split(b"\n", 1)[0].decode("utf-8"))
            reply = {"id": req["id"], "ok": True, "result": {"ok": True}, "sync": []}
            self._replies.append((json.dumps(reply) + "\n").encode("utf-8"))

        def recv(self, n: int) -> bytes:
            if not self._replies:
                return b""
            return self._replies.pop(0)

        def close(self) -> None:
            return None

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(ws_cli, "bridge_for_parent", bridge)
    monkeypatch.setattr(
        ws_cli,
        "starting_for_parent",
        lambda parent_pid=None: {"desk": "alice", "pid": 42, "parent_pid": 7},
    )
    monkeypatch.setattr(ws_cli, "_pid_alive", lambda pid: True)
    monkeypatch.setattr(ws_cli.time, "sleep", lambda s: sleeps.append(float(s)))
    monkeypatch.setattr(ws_cli.socket, "create_connection", lambda *a, **k: _Sock())

    out = ws_cli.mill_ws_call({"verb": "inbox"}, token="t", desk="alice")
    assert out["ok"] is True
    assert sleeps == [ws_cli.CONNECT_START_POLL_S]
    assert 0.5 not in sleeps


def test_dead_starting_connect_uses_the_short_retry(monkeypatch) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr(ws_cli, "bridge_for_parent", lambda parent_pid=None: None)
    monkeypatch.setattr(
        ws_cli,
        "starting_for_parent",
        lambda parent_pid=None: {"desk": "alice", "pid": 9, "parent_pid": 1},
    )
    monkeypatch.setattr(ws_cli, "_pid_alive", lambda pid: False)
    monkeypatch.setattr(ws_cli, "SITTING_BRIDGE_RETRY_WAIT_S", 0.5)
    monkeypatch.setattr(ws_cli.time, "sleep", lambda s: sleeps.append(float(s)))
    with pytest.raises(CoordError) as ei:
        ws_cli.mill_ws_call({"verb": "inbox"}, token="t", desk="alice")
    assert str(ei.value) == SESSION_WS_BRIDGE_REQUIRED
    assert sleeps == [0.5]


def test_ready_line_prints_once(capsys) -> None:
    ws_cli._READY_DESKS.clear()
    ws_cli.note_bridge_ready("alice")
    ws_cli.note_bridge_ready("alice")
    lines = [ln for ln in capsys.readouterr().out.splitlines() if ln.strip()]
    assert len(lines) == 1
    row = json.loads(lines[0])
    assert row["ready"] is True and row["desk"] == "alice"
    assert "same parent shell" in row["note"]


def test_wait_for_sitting_desk_polls_only_while_starting(monkeypatch) -> None:
    sleeps: list[float] = []
    n = {"n": 0}

    def bridge(parent_pid=None):
        n["n"] += 1
        if n["n"] < 2:
            return None
        return {"desk": "alice"}

    monkeypatch.setattr(ws_cli, "bridge_for_parent", bridge)
    monkeypatch.setattr(
        ws_cli,
        "starting_for_parent",
        lambda parent_pid=None: {"desk": "alice", "pid": 4, "parent_pid": 1},
    )
    monkeypatch.setattr(ws_cli, "_pid_alive", lambda pid: True)
    monkeypatch.setattr(ws_cli.time, "sleep", lambda s: sleeps.append(float(s)))
    assert ws_cli.wait_for_sitting_desk() == "alice"
    assert sleeps == [ws_cli.CONNECT_START_POLL_S]

    sleeps.clear()
    monkeypatch.setattr(ws_cli, "starting_for_parent", lambda parent_pid=None: None)
    monkeypatch.setattr(ws_cli, "bridge_for_parent", lambda parent_pid=None: None)
    monkeypatch.setattr(ws_cli, "SITTING_BRIDGE_RETRY_WAIT_S", 0.5)
    monkeypatch.setattr(ws_cli, "SITTING_FIRST_WAIT_S", 0.3)
    # 0.7.x: no starting file yet -> keep looking for a connect launched just before.
    assert ws_cli.wait_for_sitting_desk() == ""
    assert sleeps and set(sleeps) == {ws_cli.CONNECT_START_POLL_S}


def test_command_finds_a_connect_that_starts_after_it(monkeypatch) -> None:
    """`mill connect DESK & mill COMMAND`: the starting file appears a moment later."""
    seen = {"n": 0}

    def starting(parent_pid=None):
        seen["n"] += 1
        return {"desk": "alice", "pid": 4, "parent_pid": 1} if seen["n"] > 2 else None

    calls = {"n": 0}

    def bridge(parent_pid=None):
        calls["n"] += 1
        return {"desk": "alice"} if seen["n"] > 3 else None

    monkeypatch.setattr(ws_cli, "starting_for_parent", starting)
    monkeypatch.setattr(ws_cli, "bridge_for_parent", bridge)
    monkeypatch.setattr(ws_cli, "_pid_alive", lambda pid: True)
    monkeypatch.setattr(ws_cli.time, "sleep", lambda s: None)
    monkeypatch.setattr(ws_cli, "SITTING_BRIDGE_RETRY_WAIT_S", 0.5)
    assert ws_cli.wait_for_sitting_desk() == "alice"


def test_sitting_miss_permanent_fails_after_one_retry(monkeypatch) -> None:
    """#121 GO A: still missing after one wait -> fail closed with same error."""
    sleeps: list[float] = []
    lookups = {"n": 0}

    def always_miss(parent_pid=None):
        lookups["n"] += 1
        return None

    monkeypatch.setattr(ws_cli, "bridge_for_parent", always_miss)
    monkeypatch.setattr(ws_cli, "SITTING_BRIDGE_RETRY_WAIT_S", 0.5)
    monkeypatch.setattr(ws_cli.time, "sleep", lambda s: sleeps.append(float(s)))

    with pytest.raises(CoordError) as ei:
        ws_cli.mill_ws_call({"verb": "inbox"}, token="t", desk="DESK_alice")
    assert str(ei.value) == SESSION_WS_BRIDGE_REQUIRED
    assert lookups["n"] == 2
    assert sleeps == [0.5]


def test_other_errors_not_retried(monkeypatch) -> None:
    """#121 GO A: only the exact sitting-miss string is retried."""
    sleeps: list[float] = []
    monkeypatch.setattr(ws_cli, "SITTING_BRIDGE_RETRY_WAIT_S", 0.5)
    monkeypatch.setattr(ws_cli.time, "sleep", lambda s: sleeps.append(float(s)))

    with pytest.raises(CoordError) as ei:
        ws_cli.mill_ws_call({"verb": "join"}, token="t", desk="DESK_alice")
    assert "join stays HTTP only" in str(ei.value)
    assert sleeps == []

    with pytest.raises(CoordError) as ei2:
        ws_cli.mill_ws_call({}, token="t", desk="DESK_alice")
    assert "bad id" in str(ei2.value).lower() or "verb" in str(ei2.value).lower()
    assert str(ei2.value) != SESSION_WS_BRIDGE_REQUIRED
    assert sleeps == []


def _reply_socket(payload: dict):
    """Bridge socket that answers one RPC with payload plus the request id."""

    class _Sock:
        def __init__(self) -> None:
            self._replies: list[bytes] = []

        def settimeout(self, _t: float) -> None:
            return None

        def sendall(self, data: bytes) -> None:
            req = json.loads(data.split(b"\n", 1)[0].decode("utf-8"))
            reply = dict(payload)
            reply["id"] = req["id"]
            self._replies.append((json.dumps(reply) + "\n").encode("utf-8"))

        def recv(self, _n: int) -> bytes:
            if not self._replies:
                return b""
            return self._replies.pop(0)

        def close(self) -> None:
            return None

        def __enter__(self):
            return self

        def __exit__(self, *_a):
            return False

    def fake_connect(addr, timeout=None):
        assert addr[0] == "127.0.0.1"
        return _Sock()

    return fake_connect


def test_refused_hold_bridge_reply_stays_on_stdout(monkeypatch, capsys) -> None:
    """A refused hold over the bridge exits 1 and keeps the row on stdout (#207)."""
    from types import SimpleNamespace

    from agent_coord.client import http

    ws_cli.write_rpc_bridge("alice", port=12345, secret="bridge-secret", pid=os.getpid())
    monkeypatch.setattr(
        ws_cli.socket,
        "create_connection",
        _reply_socket(
            {
                "ok": False,
                "result": {
                    "ok": False,
                    "held": False,
                    "owner": "builder",
                    "resource": "agent_coord/client/ws.py",
                },
                "sync": [],
            }
        ),
    )
    monkeypatch.setattr("agent_coord.client.http.mill_url", lambda: "http://127.0.0.1:9")
    monkeypatch.setattr(
        "agent_coord.client.http.resolve_desk_owner", lambda *_a, **_k: "alice"
    )
    monkeypatch.setattr("agent_coord.client.http.mill_api_key", lambda _who: "k")
    monkeypatch.setattr(
        "agent_coord.client.outbound.body_from_args",
        lambda _args: {"verb": "hold"},
    )
    rc = http.mill_http_from_args(SimpleNamespace(cmd="hold"))
    captured = capsys.readouterr()
    assert rc == 1
    assert captured.err == ""
    out = json.loads(captured.out)
    assert out["ok"] is False
    assert out["result"]["held"] is False
    assert out["result"]["reason"] == "held by builder, not you"
    captured.out.encode("ascii")


def test_bridge_error_envelope_still_raises(monkeypatch) -> None:
    """ok false with an error string and no result still raises (#207)."""
    ws_cli.write_rpc_bridge("alice", port=12345, secret="bridge-secret", pid=os.getpid())
    monkeypatch.setattr(
        ws_cli.socket,
        "create_connection",
        _reply_socket({"ok": False, "error": "book down", "sync": []}),
    )
    with pytest.raises(CoordError, match="book down"):
        ws_cli.mill_ws_call({"verb": "inbox"}, token="t", desk="alice")


def test_taken_hold_bridge_stays_stdout(monkeypatch, capsys) -> None:
    """An ok true hold with held true is unchanged on stdout (#207)."""
    from types import SimpleNamespace

    from agent_coord.client import http

    ws_cli.write_rpc_bridge("alice", port=12345, secret="bridge-secret", pid=os.getpid())
    monkeypatch.setattr(
        ws_cli.socket,
        "create_connection",
        _reply_socket(
            {
                "ok": True,
                "result": {"ok": True, "held": True, "owner": "grok-tui"},
                "sync": [],
            }
        ),
    )
    monkeypatch.setattr("agent_coord.client.http.mill_url", lambda: "http://127.0.0.1:9")
    monkeypatch.setattr(
        "agent_coord.client.http.resolve_desk_owner", lambda *_a, **_k: "alice"
    )
    monkeypatch.setattr("agent_coord.client.http.mill_api_key", lambda _who: "k")
    monkeypatch.setattr(
        "agent_coord.client.outbound.body_from_args",
        lambda _args: {"verb": "hold"},
    )
    rc = http.mill_http_from_args(SimpleNamespace(cmd="hold"))
    captured = capsys.readouterr()
    assert rc == 0
    assert captured.err == ""
    out = json.loads(captured.out)
    assert out["ok"] is True
    assert out["result"]["held"] is True



def _reply_socket_keep_id(payload: dict):
    """Like _reply_socket but keeps payload id (for mismatch tests #66)."""

    class _Sock:
        def __init__(self) -> None:
            self._replies: list[bytes] = []

        def settimeout(self, _t: float) -> None:
            return None

        def sendall(self, data: bytes) -> None:
            self._replies.append((json.dumps(payload) + "\n").encode("utf-8"))

        def recv(self, _n: int) -> bytes:
            if not self._replies:
                return b""
            return self._replies.pop(0)

        def close(self) -> None:
            return None

        def __enter__(self):
            return self

        def __exit__(self, *_a):
            self.close()
            return False

    return lambda *_a, **_k: _Sock()


def test_bridge_close_error_names_superseded() -> None:
    """4000/4401 become honest in-flight errors; other closes stay generic (#66)."""

    class Closed(Exception):
        def __init__(self, code: int) -> None:
            self.rcvd = type("R", (), {"code": code})()

    assert "superseded (4000)" in ws_cli.bridge_close_error(Closed(4000))
    assert "mill connect again" in ws_cli.bridge_close_error(Closed(4000))
    assert "token rejected (4401)" in ws_cli.bridge_close_error(Closed(4401))
    assert ws_cli.bridge_close_error(Closed(1006)) == "ws rpc: sitting socket closed"
    assert ws_cli.bridge_close_error(None) == "ws rpc: sitting socket closed"


def test_mill_ws_call_mismatch_prefers_bridge_error(monkeypatch) -> None:
    """A mismatched reply still surfaces the bridge error text (#66)."""
    ws_cli.write_rpc_bridge("alice", port=12345, secret="bridge-secret", pid=os.getpid())
    monkeypatch.setattr(
        ws_cli.socket,
        "create_connection",
        _reply_socket_keep_id(
            {
                "id": "other-id",
                "ok": False,
                "error": "ws rpc: superseded (4000): another connect took this seat; mill connect again",
            }
        ),
    )
    with pytest.raises(CoordError, match="superseded \\(4000\\)"):
        ws_cli.mill_ws_call({"verb": "inbox"}, token="t", desk="alice")


def test_mill_ws_call_mismatch_without_error_hints_reconnect(monkeypatch) -> None:
    ws_cli.write_rpc_bridge("alice", port=12345, secret="bridge-secret", pid=os.getpid())
    monkeypatch.setattr(
        ws_cli.socket,
        "create_connection",
        _reply_socket_keep_id({"id": "other-id", "ok": False}),
    )
    with pytest.raises(CoordError, match="bridge reply id mismatch"):
        ws_cli.mill_ws_call({"verb": "inbox"}, token="t", desk="alice")
    # Fresh call: same hint
    monkeypatch.setattr(
        ws_cli.socket,
        "create_connection",
        _reply_socket_keep_id({"id": "other-id", "ok": True, "result": {}}),
    )
    with pytest.raises(CoordError, match="mill connect again"):
        ws_cli.mill_ws_call({"verb": "todo"}, token="t", desk="alice")


def test_foreground_tip_only_on_a_terminal(monkeypatch) -> None:
    class Tty:
        def isatty(self):
            return True

    class Pipe:
        def isatty(self):
            return False

    monkeypatch.setattr(ws_cli.sys, "stdin", Tty())
    monkeypatch.setattr(ws_cli.sys, "stderr", Tty())
    tip = ws_cli.foreground_tip("alice")
    assert "bash -c 'mill connect alice >/dev/null 2>&1 & trap \"kill $!\" EXIT; mill COMMAND ARGS'" in tip
    assert "blocks" in tip
    monkeypatch.setattr(ws_cli.sys, "stdin", Pipe())
    assert ws_cli.foreground_tip("alice") == ""
