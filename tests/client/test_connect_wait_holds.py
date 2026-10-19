"""Card #278: connect-wait with nothing queued keeps waiting for the next hint.

Regression row F28 (connect-wait-holds). The docs (skill.md, JOIN.md,
cli-desk.md, connect.md) say it waits; the foreground path now does.
"""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from agent_coord.client import ws as ws_client
from agent_coord.client.http import mill_here_over_http
from tests.client.test_mill_hold import _patch_socket

ROOT = Path(__file__).resolve().parents[2]


def _args():
    return SimpleNamespace(cmd="connect", desk="builder", project="", doing="present", role="",
                           root="", reset=False, vendor="", session="", foreground=True)


def test_connect_wait_asks_to_hold_an_empty_queue(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    monkeypatch.setattr("agent_coord.client.tokens.read_session_token", lambda owner, **k: "seat")
    seen = {}

    def _wait(desk, token, **kw):
        seen.update(kw)
        return {"ok": True, "mode": "hold", "hint": {"hint": "MAIL", "type": "mail", "id": 7}}

    monkeypatch.setattr("agent_coord.client.ws.wait_one_hint", _wait)
    assert mill_here_over_http(_args()) == 0
    assert seen["hold_empty_sync"] is True
    assert json.loads(capsys.readouterr().out.strip().splitlines()[-1])["hint"]["id"] == 7


def test_nothing_queued_waits_for_the_next_hint(monkeypatch):
    _patch_socket(monkeypatch, [json.dumps({"kind": "sync", "sync": []}),
                                json.dumps({"hint": "MAIL", "type": "mail", "id": 9})])
    got = ws_client.wait_one_hint("x", "tok", skip_ping=True, timeout_s=5, hold_empty_sync=True)
    assert got["ok"] is True and got["hint"]["id"] == 9


def test_nothing_queued_and_no_hint_does_not_return_an_empty_sync(monkeypatch):
    _patch_socket(monkeypatch, [json.dumps({"kind": "sync", "sync": []})])
    got = ws_client.wait_one_hint("x", "tok", skip_ping=True, timeout_s=0.4, hold_empty_sync=True)
    assert got["ok"] is False and got["error"] == "timeout"


def test_docs_agree_connect_wait_waits():
    join = (ROOT / "docs" / "JOIN.md").read_text(encoding="utf-8")
    skill = (ROOT / "docs" / "protocol" / "skill.md").read_text(encoding="utf-8")
    cli = (ROOT / "docs" / "protocol" / "cli-desk.md").read_text(encoding="utf-8")
    conn = (ROOT / "docs" / "protocol" / "connect.md").read_text(encoding="utf-8")
    bot = (ROOT / "docs" / "protocol" / "models" / "grok-bot" / "SKILL.md").read_text(encoding="utf-8")
    assert "waits for the next hint" in join
    assert "the next hint when nothing is" in skill
    assert "An empty queue keeps waiting" in cli
    assert "an empty queue keeps waiting" in conn
    assert "Regression row F28 (connect-wait-holds)" in conn
    assert "returns on an empty list" not in bot
