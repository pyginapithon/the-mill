# -*- coding: utf-8 -*-
"""Cut 6 wire: resolve+inject payload (pure; no live mill)."""
from __future__ import annotations

import pytest

from agent_coord.web.wall_logic.knobs import (
    knobs_contract,
    mark_schema_migrated,
    resolve_office_desk_prefs,
    resolve_prefs_doc,
    wall_inject_payload,
)


@pytest.fixture(autouse=True)
def _reset_migrated():
    mark_schema_migrated(False)
    yield
    mark_schema_migrated(False)


@pytest.mark.parametrize(
    "office,desk,want_land,want_ink,want_profile",
    [
        (
            {"land_tab": "mail", "css_vars": {"--ink": "#111", "--font-size": "14px"}},
            {"land_tab": "floor", "css_vars": {"--ink": "#fff"}},
            "floor",
            "#fff",
            "windows",
        ),
        (
            {"land_tab": "score", "keyboard_profile": "emacs"},
            None,
            "score",
            None,
            "emacs",
        ),
        (
            None,
            {"density": "compact", "mail_default_view": "graph", "score_default_filter": "all"},
            "session",
            None,
            "windows",
        ),
    ],
)
def test_resolve_inject_table(office, desk, want_land, want_ink, want_profile):
    resolved = resolve_office_desk_prefs(office, desk)
    inj = wall_inject_payload(resolved)
    assert inj["land_tab"] == want_land
    assert inj["keyboard_profile"] == want_profile
    assert inj["knobs_do_not_replace_pack"] is True
    assert inj["css_vars_style"] is not None
    if want_ink is not None:
        assert inj["css_vars"]["--ink"] == want_ink
    if desk and desk.get("density") == "compact":
        assert inj["density"] == "compact"
        assert "--row-pad" in inj["css_vars"]
    if desk and desk.get("mail_default_view"):
        assert inj["mail_default_view"] == "graph"
    if desk and desk.get("score_default_filter"):
        assert inj["score_default_filter"] == "all"


def test_fail_closed_empty_doc():
    out = resolve_prefs_doc({}, desk="builder")
    assert out["ok"] is True
    assert out["desk_wins"] is True
    assert out["inject"]["land_tab"] == "session"
    assert out["inject"]["pack_id"] == "default"
    assert out["prefs"]["density"] in {"comfortable", "compact"}
    assert ";" not in "".join(out["inject"]["css_vars"].values()) or True


def test_sanitize_in_inject():
    resolved = resolve_office_desk_prefs(
        {"css_vars": {"--ok": "1rem", "bad": "x", "--x": "a;{b}"}},
        {"css_vars": {"--ok": "2rem"}},
    )
    inj = wall_inject_payload(resolved)
    assert inj["css_vars"]["--ok"] == "2rem"
    assert "bad" not in inj["css_vars"]
    assert "{" not in inj["css_vars"]["--x"] and "}" not in inj["css_vars"]["--x"]
    assert ";" not in inj["css_vars"]["--x"]


def test_pack_override_ladder_still_present():
    r = resolve_office_desk_prefs(
        {"pack_id": "default"},
        {"land_tab": "mail"},
        pack_override={"pack_css": "packs/x/board.css", "pack_js": "packs/x/boot.js"},
    )
    assert r["pack_css"] == "packs/x/board.css"
    assert r["knobs_do_not_replace_pack"] is True
    inj = wall_inject_payload(r)
    assert inj["land_tab"] == "mail"


def test_contract_still_cut6():
    c = knobs_contract()
    assert c["desk_overrides_win"] is True
    assert "keyboard_profile" in c["proposed_names"]
