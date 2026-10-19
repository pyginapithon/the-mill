"""A refused first open uses reconnect backoff and prints JSON (#139)."""
from __future__ import annotations

import json

from agent_coord.client import ws as ws_cli


def test_open_retry_notice_is_json_with_host_and_class():
    line = ws_cli.open_retry_notice("127.0.0.1", ConnectionRefusedError(111, "refused"))
    row = json.loads(line)
    assert row == {"backchannel": "reconnect", "host": "127.0.0.1", "error": "ConnectionRefusedError"}
    assert line.startswith("{")
    line.encode("ascii")


def test_ws_host_drops_the_path():
    assert ws_cli.ws_host("wss://office.example/ws/grok-tui") == "office.example"
    assert ws_cli.ws_host("ws://127.0.0.1:8765/ws/grok-tui") == "127.0.0.1"


def test_first_open_uses_the_shared_backoff():
    assert ws_cli.reconnect_delay_s(0, jitter=0.0) == 1.0
    assert ws_cli.reconnect_delay_s(6, jitter=0.0) == 60.0
