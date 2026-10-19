# -*- coding: utf-8 -*-
"""Table-driven wall keyboard profiles / effective map / overrides / conflict."""
from __future__ import annotations

import pytest

from agent_coord.web.wall_logic.keys import (
    ACTION_IDS,
    BROWSER_RESERVED,
    DEFAULT_PROFILE,
    PROFILES,
    effective_map,
    find_conflicts,
    keys_contract,
    load_state,
    normalize_chord,
    profile_map,
    reset_action,
    reset_all,
    set_override,
    set_profile,
    storage_key,
    cursor_defaults_avoid_ctrl_l,
)


def test_contract_path_a_no_schema():
    c = keys_contract()
    assert c["path"] == "A"
    assert c["schema_migrated"] is False
    assert c["default_profile"] == "windows"
    assert c["profiles"] == list(PROFILES)
    assert c["cursor_avoids_ctrl_l"] is True


@pytest.mark.parametrize(
    "raw,want",
    [
        ("alt+1", "Alt+1"),
        ("Ctrl+p", "Ctrl+P"),
        ("C-g", "Ctrl+G"),
        ("?", "?"),
        ("Escape", "Escape"),
        ("f5", "F5"),
        ("", ""),
    ],
)
def test_normalize_chord(raw, want):
    assert normalize_chord(raw) == want


def test_storage_key_per_desk():
    assert storage_key("builder") == "wall-keys:builder"
    assert storage_key("alice") != storage_key("bob")


def test_default_windows_map():
    m = effective_map(None)
    assert m["pane.session"] == "Alt+1"
    assert m["pane.refresh"] == "F5"
    assert m["ui.help"] == "?"
    assert m["ui.cancel"] == "Escape"
    assert find_conflicts(m) == []


@pytest.mark.parametrize("profile", list(PROFILES))
def test_each_profile_no_internal_conflict(profile):
    m = effective_map({"profile": profile, "overrides": {}})
    assert find_conflicts(m) == []
    for aid in ("pane.session", "ui.help", "ui.cancel"):
        assert aid in m and m[aid]


def test_cursor_avoids_ctrl_l():
    m = profile_map("cursor")
    assert "Ctrl+L" not in m.values()
    assert "Meta+L" not in m.values()
    assert cursor_defaults_avoid_ctrl_l()


def test_vscode_palette_ctrl_p():
    m = profile_map("vscode")
    assert m["ui.help"] == "Ctrl+P"


def test_bot_bare_letters():
    m = profile_map("bot")
    assert m["pane.session"] == "s"
    assert m["pane.floor"] == "f"


def test_overrides_and_reset():
    st = load_state({"profile": "windows", "overrides": {}})
    st2 = set_override(st, "pane.mail", "Alt+0")
    eff = effective_map(st2)
    assert eff["pane.mail"] == "Alt+0"
    st3 = reset_action(st2, "pane.mail")
    assert "pane.mail" not in st3["overrides"]
    assert effective_map(st3)["pane.mail"] == profile_map("windows")["pane.mail"]
    st4 = set_override(st3, "pane.guide", "Alt+G")
    st5 = reset_all(st4)
    assert st5["overrides"] == {}


def test_conflict_warns_unless_confirmed():
    st = {"profile": "windows", "overrides": {}}
    # Alt+1 is pane.session - binding pane.floor to Alt+1 conflicts
    with pytest.raises(ValueError, match="conflict"):
        set_override(st, "pane.floor", "Alt+1", confirm_clobber=False)
    st2 = set_override(st, "pane.floor", "Alt+1", confirm_clobber=True)
    assert st2["overrides"]["pane.floor"] == "Alt+1"
    conflicts = find_conflicts(effective_map(st2))
    assert any(c["chord"] == "Alt+1" for c in conflicts)


def test_browser_reserved_rejected():
    with pytest.raises(ValueError, match="reserved"):
        set_override({"profile": "windows"}, "pane.session", "Ctrl+T")


def test_two_desks_independent_state_shape():
    a = load_state({"profile": "brief", "overrides": {"pane.mail": "Alt+E"}})
    b = load_state({"profile": "emacs", "overrides": {}})
    assert a["profile"] != b["profile"]
    assert storage_key("desk-a") != storage_key("desk-b")


def test_set_profile():
    st = set_profile({"profile": "windows", "overrides": {"pane.mail": "Alt+0"}}, "bot", keep_overrides=True)
    assert st["profile"] == "bot"
    assert st["overrides"]["pane.mail"] == "Alt+0"
    st2 = set_profile(st, "windows", keep_overrides=False)
    assert st2["overrides"] == {}


def test_action_ids_stable():
    for aid in (
        "pane.session",
        "pane.floor",
        "pane.jobs",
        "pane.score",
        "pane.mail",
        "pane.plan",
        "pane.admin",
        "pane.wire",
        "pane.guide",
        "pane.prev",
        "pane.next",
        "pane.refresh",
        "focus.filter",
        "context.new",
        "ui.help",
        "ui.cancel",
        "floor.toggleAgg",
        "floor.toggleMapTimeline",
        "mail.next",
        "mail.prev",
        "mail.open",
        "mail.markRead",
        "profile.cycle",
    ):
        assert aid in ACTION_IDS


def test_default_profile_constant():
    assert DEFAULT_PROFILE == "windows"
    assert "Ctrl+T" in BROWSER_RESERVED or "Ctrl+T" in set(BROWSER_RESERVED)
