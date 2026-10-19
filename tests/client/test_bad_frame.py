"""A non-JSON wall frame fails a waiting verb now (#141)."""
from __future__ import annotations

import asyncio
import json

from agent_coord.client import ws as ws_cli


def test_bad_frame_notice_keeps_120_chars():
    raw = "<html>502 Bad Gateway</html>" + ("x" * 200)
    row = ws_cli.bad_frame_notice(raw)
    assert row["backchannel"] == "bad_frame"
    assert row["bytes"] == len(raw.encode("utf-8"))
    assert row["head"] == raw[:120]
    assert len(row["head"]) == 120


def test_lone_rpc_fails_immediately(capsys):
    q: asyncio.Queue = asyncio.Queue(maxsize=1)
    pending = {"abc": q}
    assert ws_cli.fail_lone_rpc(pending, "<html>502 Bad Gateway</html>") is True
    assert pending == {}
    got = q.get_nowait()
    assert got["ok"] is False
    assert got["error"] == "ws rpc: bad frame"
    assert got["id"] == "abc"
    line = json.loads(capsys.readouterr().out.strip())
    assert line["backchannel"] == "bad_frame"
    assert "502" in line["head"]


def test_two_pending_rpcs_are_not_guessed():
    pending = {"a": asyncio.Queue(), "b": asyncio.Queue()}
    assert ws_cli.fail_lone_rpc(pending, "<html>") is False
    assert set(pending) == {"a", "b"}
