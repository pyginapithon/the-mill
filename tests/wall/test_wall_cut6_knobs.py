# -*- coding: utf-8 -*-
"""Cut 6 knobs: office_default + desk merge, sanitize, migrate."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent_coord.web.wall_logic.knobs import (
    CUT6_PREFS_VERSION,
    knobs_contract,
    mark_schema_migrated,
    migrate_wall_keys_into_desk,
    migrate_wall_prefs,
    migrate_wall_prefs_file,
    resolve_office_desk_prefs,
    sanitize_css_vars,
    sanitize_keyboard_overrides,
    schema_migrated,
)


@pytest.fixture(autouse=True)
def _reset_migrated():
    mark_schema_migrated(False)
    yield
    mark_schema_migrated(False)


def test_contract_lists_keyboard_and_desk_wins():
    c = knobs_contract()
    assert "keyboard_profile" in c["proposed_names"]
    assert "keyboard_overrides" in c["proposed_names"]
    assert c["desk_overrides_win"] is True
    assert c["storage"] == "mill_prefs_json"
    assert c["schema_migrated"] is False
    assert c["cut6_prefs_version"] == CUT6_PREFS_VERSION


def test_sanitize_css_vars_strip_and_prefix():
    assert sanitize_css_vars({"accent": "red", "--ok": "1px", "--bad": "a;{b}"}) == {
        "--ok": "1px",
        "--bad": "ab",
    }
    assert sanitize_css_vars(None) == {}


def test_desk_overrides_office_default():
    office = {
        "land_tab": "mail",
        "density": "compact",
        "keyboard_profile": "windows",
        "css_vars": {"--ink": "#eee"},
    }
    desk = {
        "land_tab": "floor",
        "keyboard_profile": "emacs",
        "keyboard_overrides": {"pane.mail": "Alt+0"},
        "css_vars": {"--ink": "#fff", "nope": "x"},
    }
    r = resolve_office_desk_prefs(office, desk)
    assert r["land_tab"] == "floor"
    assert r["density"] == "compact"
    assert r["keyboard_profile"] == "emacs"
    assert r["keyboard_overrides"]["pane.mail"] == "Alt+0"
    assert r["css_vars"]["--ink"] == "#fff"
    assert "nope" not in r["css_vars"]
    assert r["desk_wins"] is True


def test_office_only_when_no_desk():
    r = resolve_office_desk_prefs({"pack_id": "custom", "mail_default_view": "graph"}, None)
    assert r["pack_id"] == "custom"
    assert r["mail_default_view"] == "graph"
    assert r["keyboard_profile"] == "windows"


@pytest.mark.parametrize(
    "raw,want",
    [
        ({"pane.session": "alt+2", "bogus": "x"}, {"pane.session": "Alt+2"}),
        ({}, {}),
        (None, {}),
    ],
)
def test_sanitize_keyboard_overrides(raw, want):
    assert sanitize_keyboard_overrides(raw) == want


def test_migrate_wall_keys_into_desk():
    desk = {"density": "compact"}
    local = {"profile": "bot", "overrides": {"ui.help": "?"}}
    out = migrate_wall_keys_into_desk(desk, local)
    assert out["keyboard_profile"] == "bot"
    assert out["keyboard_overrides"]["ui.help"] == "?"
    assert out["density"] == "compact"


def test_migrate_wall_prefs_legacy_normal_density():
    doc = {"office_default": None, "prefs": {"density": "normal", "land_tab": "jobs"}}
    m = migrate_wall_prefs(doc)
    assert m["version"] == 6
    assert m["office_default"]["density"] == "comfortable"
    assert m["office_default"]["land_tab"] == "jobs"
    assert m["office_default"]["keyboard_profile"] == "windows"
    assert m["prefs"] is None
    assert m["desks"] == {}


def test_migrate_wall_prefs_file_marks_schema(tmp_path: Path):
    pref = tmp_path / "wall_prefs.json"
    pref.write_text(json.dumps({"office_default": None, "prefs": {"density": "normal"}}), encoding="utf-8")
    assert schema_migrated() is False
    out = migrate_wall_prefs_file(pref, mark=True)
    assert out["version"] == 6
    assert schema_migrated() is True
    assert knobs_contract()["schema_migrated"] is True
    loaded = json.loads(pref.read_text(encoding="utf-8"))
    assert loaded["version"] == 6
