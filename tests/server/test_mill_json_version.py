# -*- coding: utf-8 -*-
"""Throwaway: every top-level mill JSON carries mill version (no live SQL)."""
from __future__ import annotations

import asyncio
import json
from typing import Any

import pytest

from agent_coord import __version__
from agent_coord.install.packver import package_version
from agent_coord.server.mill_json import dumps_mill, mill_version, stamp_mill
from agent_coord.server.middleware import _json
from agent_coord.server.push import HUB


def test_version_source_agrees() -> None:
    ver = mill_version()
    assert ver
    assert ver == package_version()
    assert ver == __version__
    assert ver != "None"


def test_stamp_mill_on_dict_leaves_nested_lean() -> None:
    row = {"id": "r1", "ok": True, "result": [{"id": 7, "body": "hi"}]}
    out = stamp_mill(row)
    assert out["mill"] == mill_version()
    assert out["result"] == [{"id": 7, "body": "hi"}]
    assert "mill" not in out["result"][0]


def test_stamp_mill_wraps_bare_list() -> None:
    out = stamp_mill([{"id": 1}, {"id": 2}])
    assert out == {"result": [{"id": 1}, {"id": 2}], "mill": mill_version()}


def test_middleware_json_stamps() -> None:
    raw = _json({"error": "bad json"})
    obj = json.loads(raw.decode("utf-8"))
    assert obj["error"] == "bad json"
    assert obj["mill"] == mill_version()


def test_middleware_json_list_wrap() -> None:
    raw = _json([{"g": "ROLE_Office"}])
    obj = json.loads(raw.decode("utf-8"))
    assert obj["result"] == [{"g": "ROLE_Office"}]
    assert obj["mill"] == mill_version()


def test_ws_rpc_reply_has_mill(monkeypatch) -> None:
    from agent_coord.server import asgi as asgi_mod
    from agent_coord.server.api.mill import rpc

    class _Book:
        _cn = object()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr("agent_coord.server.book.Book", lambda *a, **k: _Book())
    monkeypatch.setitem(
        rpc.HANDLERS, "inbox", lambda c, body, project, owner: [{"id": 9}]
    )

    class _WS:
        pass

    ws = _WS()
    HUB.rooms.clear()
    HUB.rooms.setdefault("DESK_alice", set()).add(ws)

    async def go() -> dict[str, Any]:
        return await asgi_mod._ws_handle_client_text(
            "DESK_alice",
            ws,
            json.dumps({"id": "t1", "verb": "inbox", "args": {}}),
        )

    try:
        reply = asyncio.run(go())
    finally:
        HUB.rooms.clear()

    assert reply["ok"] is True
    assert reply["result"] == [{"id": 9}]
    assert reply["mill"] == mill_version()
    # lean rows inside result stay unstamped
    assert "mill" not in reply["result"][0]


def test_push_broadcast_stamps_ping(monkeypatch) -> None:
    sent: list[str] = []

    class _WS:
        async def send_text(self, text: str) -> None:
            sent.append(text)

    ws = _WS()
    HUB.rooms.clear()
    HUB.rooms.setdefault("DESK_alice", set()).add(ws)

    async def go() -> None:
        await HUB._broadcast("DESK_alice", {"type": "heartbeat", "id": 0, "hint": "PING"})

    try:
        asyncio.run(go())
    finally:
        HUB.rooms.clear()

    assert len(sent) == 1
    frame = json.loads(sent[0])
    assert frame["hint"] == "PING"
    assert frame["type"] == "heartbeat"
    assert frame["mill"] == mill_version()


def test_dumps_mill_roundtrip() -> None:
    s = dumps_mill({"ok": True, "owner": "DESK_a"})
    assert json.loads(s) == {"ok": True, "owner": "DESK_a", "mill": mill_version()}
