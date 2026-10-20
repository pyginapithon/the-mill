# -*- coding: utf-8 -*-
"""Card #328: connect-wait does not end on hints a live connect already got.

Regression row F44 (connect-wait-sent). The connect sync hands back every push
since the last sync, including ones already sent to a sitting connect of this
desk (outcome sent). Those do not end the wait; an undelivered one does.
"""
from __future__ import annotations

import json

from agent_coord.client import ws as ws_client
from tests.client.test_mill_hold import _patch_socket


def _sync(*items):
    return json.dumps({"kind": "sync", "sync": list(items)})


SENT_WATCH = {"kind": "hint", "type": "todo", "id": 3, "hint": "TODO", "outcome": "sent"}
MISSED_WATCH = {"kind": "hint", "type": "todo", "id": 4, "hint": "TODO", "outcome": "missed"}
LIVE = json.dumps({"hint": "TODO", "type": "todo", "id": 9})


def test_standing_sent_watch_hints_keep_waiting_for_the_next_hint(monkeypatch):
    _patch_socket(monkeypatch, [_sync(SENT_WATCH, dict(SENT_WATCH, id=5)), LIVE])
    got = ws_client.wait_one_hint("x", "tok", skip_ping=True, timeout_s=5, hold_empty_sync=True)
    assert got["ok"] is True and got["hint"]["id"] == 9


def test_only_sent_hints_and_no_new_hint_times_out(monkeypatch):
    _patch_socket(monkeypatch, [_sync(SENT_WATCH)])
    got = ws_client.wait_one_hint("x", "tok", skip_ping=True, timeout_s=0.4, hold_empty_sync=True)
    assert got["ok"] is False and got["error"] == "timeout"


def test_a_missed_hint_still_returns_the_queue(monkeypatch):
    _patch_socket(monkeypatch, [_sync(SENT_WATCH, MISSED_WATCH), LIVE])
    got = ws_client.wait_one_hint("x", "tok", skip_ping=True, timeout_s=5, hold_empty_sync=True)
    assert got["ok"] is True and got["hint"]["kind"] == "sync"
    assert [it["id"] for it in got["hint"]["sync"]] == [3, 4]


def test_docs_name_the_sent_case():
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    conn = (root / "docs" / "protocol" / "connect.md").read_text(encoding="utf-8")
    cli = (root / "docs" / "protocol" / "cli-desk.md").read_text(encoding="utf-8")
    assert "Regression row F44 (connect-wait-sent)" in conn
    assert "outcome `sent`" in conn and "outcome `sent`" in cli
