# -*- coding: utf-8 -*-
"""Wall human-readonly gate: hide/inert write chrome; GET polls stay."""
from __future__ import annotations

from agent_coord.web.wall_logic.packs import wall_ui_root

ROOT = wall_ui_root()
BOARD = ROOT / "default" / "board.html"
BOOT = ROOT / "default" / "boot.js"
CSS = ROOT / "default" / "board.css"


def _boot() -> str:
    return BOOT.read_text(encoding="utf-8")


def _css() -> str:
    return CSS.read_text(encoding="utf-8")


def test_marker_and_helpers():
    src = _boot()
    assert "Marker: WALL_HUMAN_READONLY" in src
    assert "function wallHumanReadonly()" in src
    assert "function wallApplyHumanReadonly()" in src
    assert "wall-human-readonly" in src
    assert "factory-human-readonly" in src
    assert "human_write" in src


def test_default_on_with_escape():
    src = _boot()
    fn = src.split("function wallHumanReadonly()", 1)[1].split(
        "function wallApplyHumanReadonly()", 1
    )[0]
    assert "return true" in fn
    assert 'localStorage.getItem("factory-human-readonly")' in fn
    assert 'q.get("human_write")' in fn


def test_write_paths_gated():
    src = _boot()
    assert "if (on && wallHumanReadonly()) return" in src
    assert "if (wallHumanReadonly()) return false; /* WALL_HUMAN_READONLY */" in src
    assert "Wall is human-readonly; agents mill send / mill reply" in src
    assert "if (wallHumanReadonly()) return Promise.resolve(null)" in src
    assert 'wallHumanReadonly() ? "" : `<button type="button" class="mail-rooms-reply"' in src
    assert 'throw new Error("Wall is human-readonly")' in src
    assert "if (wallHumanReadonly()) return; /* WALL_HUMAN_READONLY */" in src


def test_get_polls_still_present():
    src = _boot()
    assert "setInterval(function () { tick(); }, 15000)" in src
    assert "/api/v1/" in src
    assert "/api/floor" not in src
    assert "wallStartFloorPoll" in src
    assert 'method: "POST"' in src


def test_css_hides_write_chrome():
    css = _css()
    assert "html.wall-human-readonly #mail-compose" in css
    assert "html.wall-human-readonly #compose-overlay" in css
    assert "html.wall-human-readonly .mail-rooms-reply" in css
    assert "html.wall-human-readonly #admin-mint" in css


def test_compose_marked_human_write():
    html = BOARD.read_text(encoding="utf-8")
    assert 'id="mail-compose"' in html
    assert 'data-human-write="1"' in html
