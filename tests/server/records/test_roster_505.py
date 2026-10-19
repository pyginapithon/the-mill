"""Catalog mint gate. Kind is project, role, label, or desk."""
from __future__ import annotations

import pytest

from agent_coord.config import mill_catalog_open
from agent_coord.helpers.errors import CoordError
from agent_coord.server.records import name as rec_name


def test_catalog_open_high_trust_proj_role_label(monkeypatch):
    monkeypatch.setattr("agent_coord.config.mill_trust", lambda: "high")
    assert mill_catalog_open("roster")
    assert mill_catalog_open("roster")
    assert mill_catalog_open("label")
    assert mill_catalog_open("desk")


def test_catalog_open_limited_blocks_proj_role(monkeypatch):
    monkeypatch.setattr("agent_coord.config.mill_trust", lambda: "limited")
    assert not mill_catalog_open("roster")
    assert not mill_catalog_open("roster")
    assert not mill_catalog_open("label")
    assert mill_catalog_open("desk")


def test_ensure_roster_existing(monkeypatch):
    monkeypatch.setattr(rec_name, "get", lambda cn, name, kind="": 42)
    assert rec_name.ensure_roster(object(), "finance", "roster") == 42


def test_ensure_roster_creates_when_open(monkeypatch):
    monkeypatch.setattr(rec_name, "get", lambda cn, name, kind="": None)
    monkeypatch.setattr("agent_coord.config.mill_catalog_open", lambda kind: True)
    monkeypatch.setattr(rec_name, "get_or_insert", lambda cn, name, kind="": 99)
    assert rec_name.ensure_roster(object(), "launchpad") == 99


def test_ensure_roster_limited_raises(monkeypatch):
    monkeypatch.setattr(rec_name, "get", lambda cn, name, kind="": None)
    monkeypatch.setattr("agent_coord.config.mill_catalog_open", lambda kind: False)
    with pytest.raises(CoordError, match="limited-trust"):
        rec_name.ensure_roster(object(), "newproj", "roster")
