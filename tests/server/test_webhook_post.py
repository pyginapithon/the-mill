# -*- coding: utf-8 -*-
"""Host webhook POST: 8s, auth headers only when a key is set.

A success is one try. A failed POST retries once when the body has idem.
"""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from agent_coord.server import push
from agent_coord.server.wake import fire_wake_hook


class _Resp:
    def read(self, _n: int = 0) -> bytes:
        return b""

    def __enter__(self):
        return self

    def __exit__(self, *_a) -> bool:
        return False


def _names(req) -> dict[str, str]:
    return {k.lower(): v for k, v in req.header_items()}


def _fanout(rows: list[dict], *, sitting: set[str], urlopen, outcomes: list[str] | None = None):
    cn = MagicMock()
    cur = MagicMock()
    cn.cursor.return_value = cur
    cur.fetchall.return_value = []
    rooms = {desk: {object()} for desk in sitting}
    notified: list[tuple[str, dict]] = []

    def capture(desk, payload):
        notified.append((desk, dict(payload)))

    def _put(cn, desk, kind, payload, outcome):
        if outcomes is not None:
            outcomes.append(outcome)
        return []

    with patch("agent_coord.server.records.watcher.select", return_value=rows), patch(
        "agent_coord.server.records.activity.select",
        return_value=[],
    ), patch("agent_coord.server.records.push.put", _put), patch.object(
        push.HUB, "rooms", rooms
    ), patch.object(push.HUB, "notify", side_effect=capture), patch(
        "urllib.request.urlopen", urlopen
    ):
        push.fanout(cn, "todo", 14, "TODO")
    return notified


def test_fanout_webhook_posts_once_with_key(monkeypatch, caplog) -> None:
    monkeypatch.setenv("AGENT_COORD_WEBHOOK_KEY", "unit-key")
    seen: list[tuple] = []

    def urlopen(req, timeout=0):
        seen.append((req, timeout))
        return _Resp()

    rows = [
        {
            "desk": "DESK_away",
            "hint": "need",
            "delivery_mode": "webhook",
            "endpoint_url": "http://127.0.0.1/hook",
        }
    ]
    with caplog.at_level("DEBUG"):
        notified = _fanout(rows, sitting=set(), urlopen=urlopen)
    assert notified == []
    assert len(seen) == 1
    req, timeout = seen[0]
    assert timeout == 8
    assert req.get_method() == "POST"
    raw = dict(req.header_items())
    headers = _names(req)
    assert headers["content-type"] == "application/json"
    assert raw["Authorization"] == "Bearer unit-key"
    assert raw["X-Automation-Key"] == "unit-key"
    assert "X-automation-key" not in raw
    body = json.loads(req.data.decode("utf-8"))
    assert body["type"] == "todo"
    assert body["id"] == 14
    assert body["hint"] == "TODO"
    assert body["detail"] == "need"
    assert "unit-key" not in caplog.text


def test_fanout_webhook_omits_auth_when_key_unset(monkeypatch) -> None:
    monkeypatch.delenv("AGENT_COORD_WEBHOOK_KEY", raising=False)
    seen: list[tuple] = []

    def urlopen(req, timeout=0):
        seen.append((req, timeout))
        return _Resp()

    rows = [
        {
            "desk": "DESK_away",
            "hint": None,
            "delivery_mode": "webhook",
            "endpoint_url": "http://127.0.0.1/hook",
        }
    ]
    _fanout(rows, sitting=set(), urlopen=urlopen)
    assert len(seen) == 1
    req, timeout = seen[0]
    assert timeout == 8
    headers = _names(req)
    assert "authorization" not in headers
    assert "x-automation-key" not in headers
    assert headers["content-type"] == "application/json"


def test_sitting_desk_does_not_post(monkeypatch) -> None:
    monkeypatch.setenv("AGENT_COORD_WEBHOOK_KEY", "unit-key")
    seen: list = []

    def urlopen(req, timeout=0):
        seen.append(req)
        return _Resp()

    rows = [
        {
            "desk": "DESK_sit",
            "hint": None,
            "delivery_mode": "webhook",
            "endpoint_url": "http://127.0.0.1/hook",
        }
    ]
    notified = _fanout(rows, sitting={"DESK_sit"}, urlopen=urlopen)
    assert seen == []
    assert [desk for desk, _payload in notified] == ["DESK_sit"]


def test_fire_wake_hook_without_key_stays_unsigned(monkeypatch) -> None:
    """Client poke calls fire_wake_hook with no key. Env must not add headers."""
    monkeypatch.setenv("AGENT_COORD_WEBHOOK_KEY", "unit-key")
    seen: list[tuple] = []

    def urlopen(req, timeout=0):
        seen.append((req, timeout))
        return _Resp()

    with patch("urllib.request.urlopen", urlopen):
        assert fire_wake_hook("http://127.0.0.1/hook", {"type": "todo", "id": 1}, timeout=0.3) is True
    req, timeout = seen[0]
    assert timeout == 0.3
    headers = _names(req)
    assert "authorization" not in headers
    assert "x-automation-key" not in headers


def _away_row() -> dict:
    return {
        "desk": "DESK_away",
        "hint": "need",
        "delivery_mode": "webhook",
        "endpoint_url": "http://127.0.0.1/hook?token=querysecret",
    }


def _fail_lines(caplog) -> str:
    return "\n".join(
        rec.getMessage() for rec in caplog.records if rec.getMessage().startswith("webhook fail")
    )


def test_fanout_webhook_http_error_is_not_sent(monkeypatch, caplog, tmp_path) -> None:
    import urllib.error

    monkeypatch.delenv("AGENT_COORD_WEBHOOK_KEY", raising=False)
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))

    def urlopen(req, timeout=0):
        raise urllib.error.HTTPError(req.full_url, 503, "nope", hdrs=None, fp=None)

    outcomes: list[str] = []
    with caplog.at_level("INFO", logger="mill.push"):
        notified = _fanout([_away_row()], sitting=set(), urlopen=urlopen, outcomes=outcomes)
    assert notified == []
    assert outcomes == ["error"]
    line = _fail_lines(caplog)
    assert "status=503" in line
    assert "desk=DESK_away" in line
    assert "id=14" in line
    assert "127.0.0.1" not in line
    assert "querysecret" not in line


def test_fanout_webhook_timeout_is_not_sent(monkeypatch, caplog, tmp_path) -> None:
    monkeypatch.delenv("AGENT_COORD_WEBHOOK_KEY", raising=False)
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))

    def urlopen(req, timeout=0):
        raise TimeoutError("timed out")

    outcomes: list[str] = []
    with caplog.at_level("INFO", logger="mill.push"):
        notified = _fanout([_away_row()], sitting=set(), urlopen=urlopen, outcomes=outcomes)
    assert notified == []
    assert outcomes == ["error"]
    line = _fail_lines(caplog)
    assert "err=TimeoutError" in line
    assert "desk=DESK_away" in line
    assert "id=14" in line
    assert "127.0.0.1" not in line
    assert "querysecret" not in line
