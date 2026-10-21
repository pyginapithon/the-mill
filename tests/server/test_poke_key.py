# -*- coding: utf-8 -*-
"""Poke idempotency key on the live frame and the webhook POST."""
from __future__ import annotations

import urllib.error
from unittest.mock import MagicMock, patch

from agent_coord.server import push as hub
from agent_coord.server.records import push as rec_push
from agent_coord.server.wake import fire_wake_hook


def test_fanout_puts_hint_key_on_frame_and_post(monkeypatch) -> None:
    from tests.server.webhook_fixtures import arm

    arm(monkeypatch)
    notified: list[dict] = []
    posted: list[dict] = []

    def capture(desk, payload):
        notified.append(dict(payload))

    def urlopen(req, timeout=0):
        import json

        posted.append(json.loads(req.data.decode("utf-8")))
        class _Resp:
            def read(self, _n: int = 0) -> bytes:
                return b""

            def __enter__(self):
                return self

            def __exit__(self, *_a) -> bool:
                return False

        return _Resp()

    rows = [
        {"desk": "sitter", "hint": None, "delivery_mode": "polling", "endpoint_url": ""},
        {
            "desk": "away",
            "hint": None,
            "delivery_mode": "webhook",
            "endpoint_url": "http://127.0.0.1/hook",
        },
    ]
    cn = MagicMock()
    cn.cursor.return_value.fetchall.return_value = []
    with patch("agent_coord.server.records.watcher.select", return_value=rows), patch(
        "agent_coord.server.records.activity.select", return_value=[]
    ), patch("agent_coord.server.records.push.put", lambda *a, **k: []), patch.object(
        hub.HUB, "rooms", {"sitter": {object()}}
    ), patch.object(hub.HUB, "notify", side_effect=capture), patch(
        "agent_coord.server.wake._open", urlopen
    ):
        hub.fanout(cn, "todo", 119, "TODO")
    assert notified[0]["idem"] == "hint:todo:119:sitter"
    assert posted[0]["idem"] == "hint:todo:119:away"
    assert posted[0]["desk"] == "away"
    assert "desk" not in notified[0]
    assert len(posted) == 1


def test_failed_post_with_idem_retries_once() -> None:
    calls = {"n": 0}

    def urlopen(req, timeout=0):
        calls["n"] += 1
        raise urllib.error.URLError("timed out")

    with patch("agent_coord.server.wake._open", urlopen):
        assert fire_wake_hook(
            "http://127.0.0.1/hook",
            {"idem": "hint:todo:119:away"},
            timeout=0.1,
        ) is False
    assert calls["n"] == 2


def test_failed_post_without_idem_does_not_retry() -> None:
    calls = {"n": 0}

    def urlopen(req, timeout=0):
        calls["n"] += 1
        raise urllib.error.URLError("timed out")

    with patch("agent_coord.server.wake._open", urlopen):
        assert fire_wake_hook(
            "http://127.0.0.1/hook",
            {"type": "todo", "id": 1},
            timeout=0.1,
        ) is False
    assert calls["n"] == 1


def test_emit_keeps_the_key_off_the_stored_row(monkeypatch) -> None:
    stored: list[dict] = []
    notified: list[dict] = []
    monkeypatch.setattr(hub.HUB, "rooms", {"builder": {object()}})
    monkeypatch.setattr(hub.HUB, "notify", lambda desk, frame: notified.append(dict(frame)))
    monkeypatch.setattr(
        rec_push,
        "put",
        lambda cn, desk, kind, payload, outcome: stored.append(dict(payload)),
    )
    assert hub.emit(object(), "builder", "mail", {"id": 4}) == "sent"
    assert hub.emit(object(), "builder", "receipt", {"id": 4}) == "sent"
    assert notified[0]["idem"] == "letter:4:builder"
    assert notified[1]["idem"] == "receipt:4:builder"
    assert "idem" not in stored[0]
    assert "idem" not in stored[1]


def test_dispatch_ignores_a_duplicate_key(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("agent_coord.config.mill_home", lambda: tmp_path)
    calls: list[str] = []
    monkeypatch.setattr(
        "agent_coord.client.connectors.poke",
        lambda vendor, frame: calls.append(str(frame.get("idem") or "")),
    )
    from agent_coord.client import dispatch

    dispatch._SEEN.clear()
    frame = {
        "type": "todo",
        "id": 119,
        "hint": "TODO",
        "detail": "x",
        "idem": "hint:todo:119:grok-tui",
    }
    assert dispatch.dispatch_hint("poke-key-desk", frame) == "wake"
    assert dispatch.dispatch_hint("poke-key-desk", frame) == "skip"
    assert calls == ["hint:todo:119:grok-tui"]
