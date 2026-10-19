"""Gutter/split shared component (fungible cut 4)."""
from __future__ import annotations

from agent_coord.web.wall_logic.gutter import (
    BOARD_EQUIVALENT_MARKER,
    clamp_split_pct,
    floor_split_contract,
    gutter_component_paths,
    gutter_contract,
    score_split_contract,
)
from agent_coord.web.wall_logic.packs import default_board_path, pack_seam_inventory, wall_ui_root


def test_clamp_split_pct():
    assert clamp_split_pct(50) == 50.0
    assert clamp_split_pct(5, min_pct=20, max_pct=78, default=58) == 20.0
    assert clamp_split_pct(99, min_pct=20, max_pct=78, default=58) == 78.0
    assert clamp_split_pct(None, default=58) == 58.0
    assert clamp_split_pct("nope", default=42) == 42.0


def test_floor_score_contracts_distinct():
    f = floor_split_contract()
    s = score_split_contract()
    assert f["storage_key"] != s["storage_key"]
    assert f["css_var"] == "--floor-main-w"
    assert s["css_var"] == "--score-hot-w"
    assert f["keyboard"] is True
    assert s["keyboard"] is False
    assert f["apply_default_if_empty"] is True
    assert s["apply_default_if_empty"] is False
    assert f["min_pct"] <= f["default_pct"] <= f["max_pct"]
    assert s["min_pct"] <= s["default_pct"] <= s["max_pct"]


def test_gutter_component_files_exist():
    paths = gutter_component_paths()
    for p in paths.values():
        assert p.is_file(), p
    js = paths["components_js"].read_text(encoding="utf-8")
    assert "WALL_UI_COMPONENTS_GUTTER" in js
    assert "wallWireSplitGutter" in js
    assert "wireSplitGutter" in js
    # default pack mirror for deploy/_safe_static basename
    assert paths["default_js"].read_text(encoding="utf-8") == js


def test_gutter_contract_and_board_wire():
    c = gutter_contract()
    assert c["marker"] == BOARD_EQUIVALENT_MARKER
    assert c["path"] == "A"
    assert all(c["paths_exist"].values())
    board = default_board_path().read_text(encoding="utf-8")
    assert (
        'src="gutter.js"' in board
        or "src='gutter.js'" in board
        or 'src="/gutter.js"' in board
        or "src='/gutter.js'" in board
    )
    assert "gutter.css" in board
    boot = (wall_ui_root() / "default" / "boot.js").read_text(encoding="utf-8")
    assert boot.count("wallWireSplitGutter(") >= 2
    inv = pack_seam_inventory()
    assert inv["shipped"].get("p0_shared_gutter") is True
    assert (wall_ui_root() / "components" / "gutter.js").is_file()
