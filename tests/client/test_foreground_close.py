"""mill connect-wait returns JSON when the socket closes (#140)."""
from __future__ import annotations

import asyncio

from agent_coord.client import ws as ws_cli


class ConnectionClosedError(Exception):
    pass


def test_foreground_close_result_names_connect_closed():
    got = ws_cli.foreground_close_result(ConnectionClosedError("received 4401"), "grok-tui")
    assert got == {"ok": False, "error": "connect closed", "desk": "grok-tui"}
    assert ws_cli.foreground_close_result(OSError("reset"), "grok-tui")["error"] == "connect closed"
    assert ws_cli.foreground_close_result(RuntimeError("nope"), "grok-tui") is None


def test_wait_one_hint_does_not_traceback_on_close(monkeypatch):
    def _run(coro):
        coro.close()
        raise ConnectionClosedError("received 4401 (private use); then sent 4401 (private use)")

    monkeypatch.setattr(asyncio, "run", _run)
    got = ws_cli.wait_one_hint("grok-tui", "seat")
    assert got["ok"] is False
    assert got["error"] == "connect closed"
    assert "traceback" not in got["error"]
    assert "4401" not in got["error"]
