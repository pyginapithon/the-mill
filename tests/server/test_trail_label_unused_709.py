"""#709: trail --label on an unused label says it has no entries yet and points to plain first use."""
from __future__ import annotations

import pytest

from agent_coord.helpers.label_ord import unused_label


def test_high_trust_points_to_first_use():
    hint = unused_label("pack", True)
    assert hint == "label pack has no entries yet; mill label TYPE ID pack tags one (first use creates it)"
    assert "mill create label" not in hint and "no name" not in hint


def test_limited_trust_names_the_admin_create():
    hint = unused_label("pack", False)
    assert hint == "label pack has no entries yet; an Admin makes it first: mill create label pack"


class _Book:
    _cn = None


@pytest.mark.parametrize("trust,want", [("high", "first use creates it"), ("limited", "an Admin makes it first")])
def test_trail_label_unused_hint_follows_trust(monkeypatch, trust, want):
    from agent_coord.server.api.mill import rpc
    from agent_coord.server.records import name as rec_name

    monkeypatch.setenv("AGENT_COORD_TRUST", trust)
    monkeypatch.setattr(rec_name, "get", lambda *a, **k: None)
    out = rpc._h_trail(_Book(), {"label": "zz-unused"}, "unit", "a")
    assert out["rows"] == [] and out["label"] == "zz-unused"
    assert want in out["hint"] and "no name" not in out["hint"]
