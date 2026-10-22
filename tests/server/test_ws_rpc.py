# -*- coding: utf-8 -*-
"""JSON RPC over live /ws: command succeeds; kicked socket cannot complete; HTTP refused."""
from __future__ import annotations

import asyncio
import json
from typing import Any

import pytest

from agent_coord.client.session_errors import SESSION_WS_REQUIRED, SESSION_WS_RPC_ONLY
from agent_coord.helpers.errors import CoordError
from agent_coord.server import asgi as asgi_mod
from agent_coord.server.api.mill import rpc
from agent_coord.server.mill_json import mill_version
from agent_coord.server.push import HUB, WS_REPLACED, socket_seated


class _FakeWS:
    def __init__(self, name: str = "") -> None:
        self.name = name
        self.sent: list[str] = []
        self.closed: list[int] = []
        self._inbox: asyncio.Queue[str] = asyncio.Queue()

    async def send_text(self, text: str) -> None:
        self.sent.append(text)

    async def close(self, code: int = 1000) -> None:
        self.closed.append(code)

    async def receive_text(self) -> str:
        return await self._inbox.get()

    def push_client(self, obj: dict[str, Any]) -> None:
        self._inbox.put_nowait(json.dumps(obj))


class _Book:
    _tokens: dict = {}

    def __init__(self, desk: str = "alice") -> None:
        self._desk = desk
        self._cn = object()

    def resolve_bearer(self, token: str) -> str:
        return self._desk if token else ""

    def _guard_owner(self, *a, **k):
        return {}


@pytest.fixture(autouse=True)
def _clean_hub():
    HUB.rooms.clear()
    yield
    HUB.rooms.clear()


@pytest.fixture
def _no_book_mysql(monkeypatch):
    """dispatch_ws path uses Book(); keep unit tests off live MySQL."""

    class _Ctx:
        def __enter__(self):
            return _Book()

        def __exit__(self, *a):
            return False

    # Helper does: from agent_coord.server.book import Book
    monkeypatch.setattr("agent_coord.server.book.Book", lambda *a, **k: _Ctx())


def test_ws_rpc_inbox_ok(monkeypatch, _no_book_mysql) -> None:
    monkeypatch.setitem(
        rpc.HANDLERS, "inbox", lambda c, body, project, owner: [{"id": 7, "owner": owner}]
    )
    ws = _FakeWS("a")
    HUB.rooms.setdefault("alice", set()).add(ws)

    async def go() -> dict:
        return await asgi_mod._ws_handle_client_text(
            "alice",
            ws,
            json.dumps({"id": "r1", "verb": "inbox", "args": {"project": "the-mill"}}),
        )

    reply = asyncio.run(go())
    ver = mill_version()
    # #288: the reply carries its own serialized size.
    assert reply["bytes"] == len(json.dumps(reply, default=str).encode("utf-8"))
    assert reply == {
        "id": "r1",
        "ok": True,
        "result": [{"id": 7, "owner": "alice"}],
        "mill": ver,
        "sync": [],
        "bytes": reply["bytes"],
    }


def test_ws_rpc_ignores_non_rpc_text(_no_book_mysql) -> None:
    ws = _FakeWS("a")
    HUB.rooms.setdefault("alice", set()).add(ws)

    async def go() -> Any:
        a = await asgi_mod._ws_handle_client_text("alice", ws, "not-json")
        b = await asgi_mod._ws_handle_client_text(
            "alice", ws, json.dumps({"type": "heartbeat", "hint": "PING"})
        )
        return a, b

    a, b = asyncio.run(go())
    assert a is None and b is None


def test_ws_rpc_bad_shape_errors(_no_book_mysql) -> None:
    ws = _FakeWS("a")
    HUB.rooms.setdefault("alice", set()).add(ws)

    async def go() -> dict:
        return await asgi_mod._ws_handle_client_text(
            "alice", ws, json.dumps({"verb": "inbox", "args": {}})
        )

    reply = asyncio.run(go())
    assert reply["ok"] is False
    assert "id" in str(reply.get("error") or "").lower()
    assert reply.get("mill") == mill_version()
    assert reply.get("sync") == []


def test_ws_rpc_ignores_client_owner(monkeypatch, _no_book_mysql) -> None:
    monkeypatch.setitem(
        rpc.HANDLERS,
        "inbox",
        lambda c, body, project, owner: {"owner": owner, "args_owner": body.get("owner")},
    )
    ws = _FakeWS("a")
    HUB.rooms.setdefault("alice", set()).add(ws)

    async def go() -> dict:
        return await asgi_mod._ws_handle_client_text(
            "alice",
            ws,
            json.dumps(
                {
                    "id": "r2",
                    "verb": "inbox",
                    "args": {"owner": "DESK_bob", "project": "the-mill"},
                }
            ),
        )

    reply = asyncio.run(go())
    assert reply["ok"] is True
    assert reply["result"]["owner"] == "alice"
    assert reply["result"]["args_owner"] is None
    assert reply.get("mill") == mill_version()


def test_after_kick_old_socket_cannot_rpc(monkeypatch, _no_book_mysql) -> None:
    monkeypatch.setattr("agent_coord.server.push._mark_join_socket", lambda desk, *, up: None)
    monkeypatch.setitem(
        rpc.HANDLERS, "inbox", lambda c, body, project, owner: [{"id": 1}]
    )
    old, new = _FakeWS("old"), _FakeWS("new")

    async def sit() -> None:
        await HUB.add("alice", old)
        await HUB.add("alice", new)

    asyncio.run(sit())
    assert old.closed == [WS_REPLACED]
    assert socket_seated("alice", old) is False

    async def try_old() -> dict:
        return await asgi_mod._ws_handle_client_text(
            "alice",
            old,
            json.dumps({"id": "old1", "verb": "inbox", "args": {}}),
        )

    reply = asyncio.run(try_old())
    assert reply["ok"] is False
    assert reply["error"] == SESSION_WS_REQUIRED
    assert reply.get("mill") == mill_version()
    assert reply.get("sync") == []


def test_http_desk_acting_refused_without_live_ws() -> None:
    assert not HUB.rooms

    class _B(_Book):
        pass

    with pytest.raises(CoordError) as ei:
        rpc.dispatch(_B(), {"verb": "inbox", "project": "the-mill"}, token="tok")
    assert str(ei.value) == SESSION_WS_RPC_ONLY


def test_mill_ws_call_without_bridge_refuses(monkeypatch, tmp_path) -> None:
    """CLI commands require sitting mill connect bridge (no second /ws open)."""
    from agent_coord.client import ws as ws_cli
    from agent_coord.client.session_errors import SESSION_WS_BRIDGE_REQUIRED

    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    with pytest.raises(CoordError) as ei:
        ws_cli.mill_ws_call(
            {"verb": "inbox", "project": "the-mill"},
            token="tok",
            desk="alice",
        )
    assert str(ei.value) == SESSION_WS_BRIDGE_REQUIRED
