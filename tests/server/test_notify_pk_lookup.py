"""Watcher hint detail reads one activity by primary key, not the newest 40 rows."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from agent_coord.server import push

ROOT = Path(__file__).resolve().parents[2]


def _cn():
    cn = MagicMock()
    cur = MagicMock()
    cur.fetchall.return_value = []
    cn.cursor.return_value = cur
    return cn


def test_detail_is_one_pk_read_and_no_scan():
    calls = []

    def fake_get(_cn, t, i):
        calls.append((t, i))
        return {"type": t, "id": i, "created": "2026-01-02 03:04:05", "updated": None, "state": None}

    with patch("agent_coord.server.records.activity.get", side_effect=fake_get), patch(
        "agent_coord.server.records.activity.select", side_effect=AssertionError("no newest-N scan")
    ):
        d = json.loads(push._cheap_detail(_cn(), "hold", 7, []))
    assert calls == [("hold", 7)]
    assert d["when"] == "2026-01-02 03:04:05"


def test_updated_wins_over_created():
    row = {"type": "todo", "id": 3, "created": "2026-01-01 00:00:00", "updated": "2026-02-01 00:00:00"}
    with patch("agent_coord.server.records.activity.get", return_value=row):
        d = json.loads(push._cheap_detail(_cn(), "todo", 3, []))
    assert d["when"] == "2026-02-01 00:00:00"


def test_absent_activity_is_empty_when_and_null_state():
    with patch("agent_coord.server.records.activity.get", return_value=None):
        d = json.loads(push._cheap_detail(_cn(), "todo", 999999, [{"desk": "a"}]))
    assert d["when"] == "" and d["state"] is None and d["watchers"] == 1


def test_lookup_error_still_returns_detail():
    with patch("agent_coord.server.records.activity.get", side_effect=RuntimeError("down")):
        d = json.loads(push._cheap_detail(_cn(), "score", 4, []))
    assert d["what"] == "score" and d["id"] == 4 and d["when"] == ""


def test_ensure_keeps_mill_activity_get():
    src = (ROOT / "agent_coord" / "install" / "migrate.py").read_text(encoding="utf-8")
    assert '"mill_activity_get"' in src
    sql = (ROOT / "agent_coord" / "server" / "sql" / "sp_activity.sql").read_text(encoding="utf-8")
    assert "DROP PROCEDURE IF EXISTS mill_activity_get;" in sql
    wipe = (ROOT / "agent_coord" / "server" / "sql" / "wipe.sql").read_text(encoding="utf-8")
    assert "DROP PROCEDURE IF EXISTS mill_activity_get;" in wipe


def test_regression_row_f18_documented():
    doc = (ROOT / "docs" / "protocol" / "hints.md").read_text(encoding="utf-8")
    assert "Regression row F18 (notify-pk-lookup)" in doc
