# -*- coding: utf-8 -*-
"""F11: the printed connect sync keeps this desk's holds (#218)."""
from __future__ import annotations

from agent_coord.client.ws import sync_view


def test_sync_view_keeps_holds():
    msg = {
        "kind": "sync",
        "sync": [],
        "mill": "0.6.33",
        "holds": [{"resource": "docs/a.md", "since": "2026-10-12 01:02:03.000000"}],
    }
    out = sync_view(msg)
    assert out["kind"] == "sync"
    assert out["sync"] == []
    assert out["mill"] == "0.6.33"
    assert out["holds"] == msg["holds"]


def test_sync_view_missing_holds_is_empty_list():
    out = sync_view({"kind": "sync", "sync": [{"kind": "hint"}]})
    assert out["holds"] == []
    assert out["sync"] == [{"kind": "hint"}]


def test_sync_view_non_list_holds_is_empty():
    out = sync_view({"kind": "sync", "sync": [], "holds": {"resource": "x"}})
    assert out["holds"] == []
