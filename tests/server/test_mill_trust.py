# -*- coding: utf-8 -*-
"""Office trust toggle. Read is open. Set is Admin and stays on the wall."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from agent_coord.config import mill_catalog_open, mill_trust, set_mill_trust
from agent_coord.helpers.errors import CoordError
from agent_coord.server.api.mill import rpc


def test_set_mill_trust_roundtrip(tmp_path, monkeypatch) -> None:
    cfg = tmp_path / "config.toml"
    monkeypatch.setenv("AGENT_COORD_CONFIG", str(cfg))
    monkeypatch.delenv("AGENT_COORD_TRUST", raising=False)
    assert set_mill_trust("limited", cfg) == "limited"
    assert mill_trust() == "limited"
    assert mill_catalog_open("roster") is False
    assert mill_catalog_open("desk") is True
    set_mill_trust("high", cfg)
    assert mill_trust() == "high"
    assert mill_catalog_open("roster") is True


def test_trust_set_requires_admin(monkeypatch, tmp_path) -> None:
    cfg = tmp_path / "config.toml"
    monkeypatch.setenv("AGENT_COORD_CONFIG", str(cfg))
    monkeypatch.delenv("AGENT_COORD_TRUST", raising=False)

    def deny(_cn, _desk):
        raise CoordError("mill Admin required (roster Admin member)")

    monkeypatch.setattr("agent_coord.server.admin.guard.require_admin", deny)
    book = MagicMock()
    book._cn = object()
    with pytest.raises(CoordError) as ei:
        rpc._h_trust(book, {"level": "limited"}, "the-mill", "plain")
    assert str(ei.value) == "mill Admin required (roster Admin member)"
    assert not cfg.is_file()


def test_high_trust_mint_and_member_are_open(monkeypatch) -> None:
    monkeypatch.setenv("AGENT_COORD_TRUST", "high")
    monkeypatch.setattr(
        "agent_coord.server.records.name.host_put",
        lambda cn, name, kind="": [{"name": name}],
    )
    monkeypatch.setattr("agent_coord.server.records.member.put", lambda *a, **k: [{"ok": True}])
    monkeypatch.setattr(
        "agent_coord.server.admin.guard.is_role_admin",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("admin check")),
    )
    from agent_coord.server.admin.catalog import put_roster

    assert put_roster(object(), "plain", {"yes": True, "slug": "east", "confirm": "east"})
    book = MagicMock()
    book._cn = object()
    rpc._h_member(
        book,
        {"verb": "member-add", "group": "east", "desk": "other"},
        "the-mill",
        "plain",
    )


def test_limited_trust_mint_and_assign_need_admin(monkeypatch) -> None:
    monkeypatch.setenv("AGENT_COORD_TRUST", "limited")
    monkeypatch.setattr("agent_coord.server.admin.guard.is_role_admin", lambda *a, **k: False)
    from agent_coord.server.admin.catalog import put_roster

    with pytest.raises(CoordError) as ei:
        put_roster(object(), "plain", {"yes": True, "slug": "east", "confirm": "east"})
    assert str(ei.value) == "mill Admin required (roster Admin member)"
    book = MagicMock()
    book._cn = object()
    monkeypatch.setattr(
        "agent_coord.server.records.todo.find",
        lambda *a, **k: {"id": 1, "volunteer": ""},
    )
    with pytest.raises(CoordError) as ei:
        rpc._h_assign(book, {"need": "fix", "desk": "other"}, "the-mill", "plain")
    assert str(ei.value) == "mill Admin required (roster Admin member)"


def test_assign_does_not_overwrite_assignee(monkeypatch) -> None:
    monkeypatch.setenv("AGENT_COORD_TRUST", "high")
    monkeypatch.setattr("agent_coord.server.admin.guard.is_role_admin", lambda *a, **k: True)
    monkeypatch.setattr(
        "agent_coord.server.records.todo.find",
        lambda *a, **k: {"id": 1, "volunteer": "DESK_taken"},
    )
    book = MagicMock()
    book._cn = object()
    with pytest.raises(CoordError) as ei:
        rpc._h_assign(book, {"need": "fix", "desk": "other"}, "the-mill", "DESK_admin")
    assert "relinquish" in str(ei.value).lower()


def test_trust_read_does_not_require_admin(monkeypatch, tmp_path) -> None:
    cfg = tmp_path / "config.toml"
    set_mill_trust("limited", cfg)
    monkeypatch.setenv("AGENT_COORD_CONFIG", str(cfg))
    monkeypatch.delenv("AGENT_COORD_TRUST", raising=False)
    called = {"n": 0}

    def deny(_cn, _desk):
        called["n"] += 1
        raise CoordError("no")

    monkeypatch.setattr("agent_coord.server.admin.guard.require_admin", deny)
    book = MagicMock()
    book._cn = object()
    assert rpc._h_trust(book, {}, "the-mill", "DESK_plain") == {"trust": "limited"}
    assert called["n"] == 0
