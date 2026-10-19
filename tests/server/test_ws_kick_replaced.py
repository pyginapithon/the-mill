# -*- coding: utf-8 -*-
"""New mill connect on same desk seat kicks older /ws with a Disconnected reason frame."""
from __future__ import annotations

import asyncio
import json

from agent_coord.server.mill_json import mill_version
from agent_coord.server.push import Hub, WS_REPLACED, WS_REPLACED_REASON


class _FakeWS:
    def __init__(self, name: str = "") -> None:
        self.name = name
        self.sent: list[str] = []
        self.closed: list[int] = []

    async def send_text(self, text: str) -> None:
        self.sent.append(text)

    async def close(self, code: int = 1000) -> None:
        self.closed.append(code)


def test_new_connect_kicks_old_with_disconnected_reason(monkeypatch) -> None:
    monkeypatch.setattr("agent_coord.server.push._mark_join_socket", lambda desk, *, up: None)
    hub = Hub()
    old = _FakeWS("old")
    new = _FakeWS("new")

    async def go() -> None:
        await hub.add("DESK_alice", old)
        await hub.add("DESK_alice", new)

    asyncio.run(go())

    assert hub.rooms.get("DESK_alice") == {new}
    assert old.closed == [WS_REPLACED]
    assert new.closed == []
    assert len(old.sent) == 1
    frame = json.loads(old.sent[0])
    assert frame["hint"] == "DISCONNECTED"
    assert frame["type"] == "session"
    assert frame["detail"] == WS_REPLACED_REASON
    assert frame["reason"] == WS_REPLACED_REASON
    assert "tokenHash" in frame["reason"] or "superseded" in frame["reason"]
    assert frame.get("mill") == mill_version()


def test_kick_does_not_mark_socket_down_while_replacing(monkeypatch) -> None:
    marks: list[tuple[str, bool]] = []
    monkeypatch.setattr(
        "agent_coord.server.push._mark_join_socket",
        lambda desk, *, up: marks.append((desk, up)),
    )
    hub = Hub()
    a, b = _FakeWS("a"), _FakeWS("b")

    async def go() -> None:
        await hub.add("DESK_x", a)
        await hub.add("DESK_x", b)

    asyncio.run(go())
    assert marks == [("DESK_x", True)]
    assert hub.rooms.get("DESK_x") == {b}
