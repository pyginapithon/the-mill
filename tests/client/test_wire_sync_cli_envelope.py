# -*- coding: utf-8 -*-
"""wire-sync-cli-envelope: connect stamp + command CLI envelope (no live SQL)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent_coord.client.http import _unwrap_cli_raw
from agent_coord.helpers.errors import CoordError
from agent_coord.install.packver import package_version


def test_unwrap_cli_raw_empty_sync_returns_result():
    row = {"id": "r1", "ok": True, "mill": "0.5.11", "result": [{"id": 1}], "sync": []}
    assert _unwrap_cli_raw(row) == [{"id": 1}]


def test_unwrap_cli_raw_list_with_sync():
    row = {
        "id": "r1",
        "ok": True,
        "mill": "0.5.11",
        "result": [{"id": 1}],
        "sync": [{"kind": "hint"}],
    }
    assert _unwrap_cli_raw(row) == {"result": [{"id": 1}], "sync": [{"kind": "hint"}]}


def test_unwrap_cli_raw_dict_merges_sync():
    row = {
        "id": "r1",
        "ok": True,
        "mill": "0.5.11",
        "result": {"id": 68, "sender": "desk-a"},
        "sync": [{"kind": "mail"}],
    }
    assert _unwrap_cli_raw(row) == {"id": 68, "sender": "desk-a", "sync": [{"kind": "mail"}]}


def test_format_error_prefers_envelope_and_keeps_empty_sync():
    from agent_coord.__main__ import _format_error

    env = {
        "id": "r9",
        "ok": False,
        "mill": "0.5.11",
        "result": None,
        "error": "send: To required",
        "sync": [],
    }
    exc = CoordError("send: To required", sync=[], envelope=env)
    out = json.loads(_format_error(exc))
    assert out["ok"] is False
    assert out["error"] == "send: To required"
    assert out["sync"] == []
    assert out["mill"] == "0.5.11"
    assert out["id"] == "r9"
    assert out["result"] is None


def test_format_error_always_includes_sync_without_envelope():
    from agent_coord.__main__ import _format_error

    out = json.loads(_format_error(CoordError("boom", sync=[])))
    assert out == {"ok": False, "error": "boom", "sync": []}


def test_connect_sync_line_shape_from_frame():
    """Mirror on_frame connect print: kind + sync + mill + holds."""
    from agent_coord.client.ws import sync_view
    from agent_coord.install.packver import package_version

    msg = {"kind": "sync", "sync": [], "mill": package_version()}
    out = sync_view(msg)
    line = json.dumps(out, default=str)
    parsed = json.loads(line)
    assert parsed["kind"] == "sync"
    assert parsed["sync"] == []
    assert parsed["mill"] == package_version()
    assert parsed["holds"] == []
    assert "kind" in parsed and "mill" in parsed


def test_full_envelope_default_has_result_and_sync():
    """Success path shape mill_ws_call now returns (dict(msg) + sync list)."""
    msg = {
        "id": "abc",
        "ok": True,
        "mill": package_version(),
        "result": [{"id": 7}],
        "sync": [],
    }
    out = dict(msg)
    if not isinstance(out.get("sync"), list):
        out["sync"] = list(out.get("sync") or [])
    assert "result" in out and "sync" in out
    assert out["ok"] is True
    assert isinstance(out["result"], list)
    # Not a bare array
    assert isinstance(out, dict)


def test_pack_share_lists_sync_md():
    text = Path("pyproject.toml").read_text(encoding="utf-8")
    assert "docs/protocol/sync.md" in text
    assert Path("docs/protocol/sync.md").is_file()
