"""Foreground mill connect: one HINT then exit."""
from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent_coord.client import ws as ws_client


class _FakeWS:
    def __init__(self, frames):
        self._frames = list(frames)
        self._i = 0

    async def recv(self):
        if self._i >= len(self._frames):
            await asyncio.sleep(10)
            raise asyncio.TimeoutError()
        raw = self._frames[self._i]
        self._i += 1
        return raw

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False


class _ConnCM:
    def __init__(self, ws):
        self._ws = ws

    async def __aenter__(self):
        return self._ws

    async def __aexit__(self, *a):
        return False


def test_wait_one_hint_skips_ping_returns_mail():
    frames = [
        json.dumps({"hint": "PING", "type": "ping"}),
        json.dumps({"hint": "MAIL", "type": "mail", "id": 42}),
    ]
    fake = _FakeWS(frames)

    def _connect(url, **kw):
        return _ConnCM(fake)

    with patch.object(ws_client, "mill_ws_url", return_value="ws://127.0.0.1/ws/DESK_x"), patch(
        "websockets.connect", side_effect=_connect
    ), patch("agent_coord.client.inbound.ignore", side_effect=lambda m: str(m.get("hint") or "").upper() == "PING"):
        got = ws_client.wait_one_hint("x", "tok", skip_ping=True, timeout_s=5)
    assert got["ok"] is True
    assert got["mode"] == "foreground"
    assert got["hint"]["hint"] == "MAIL"
    assert got["hint"]["id"] == 42


def test_wait_one_hint_timeout():
    fake = _FakeWS([])  # only timeouts

    def _connect(url, **kw):
        return _ConnCM(fake)

    with patch.object(ws_client, "mill_ws_url", return_value="ws://127.0.0.1/ws/DESK_x"), patch(
        "websockets.connect", side_effect=_connect
    ):
        got = ws_client.wait_one_hint("x", "tok", skip_ping=True, timeout_s=0.3)
    assert got["ok"] is False
    assert got["error"] == "timeout"
