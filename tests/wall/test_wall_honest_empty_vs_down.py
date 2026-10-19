"""Table-driven: API down vs honest empty vs paint throw.

SoR: docs/acceptance/ACCEPTANCE-WALL-HONEST-EMPTY-VS-DOWN.md
"""
from __future__ import annotations

from pathlib import Path

import pytest

from agent_coord.web.wall_logic.honest import (
    MARKER,
    api_down_banner_html,
    classify_fetch,
    classify_outcome,
    honest_contract,
    honest_llm_display,
    honest_mill_bytes_display,
    sum_llm_tokens,
)
from agent_coord.web.wall_logic.score import score_pulse_counts, score_spend_pulse
from agent_coord.web.wall_logic.packs import default_board_path, default_pack_dir, wall_ui_root


def test_marker_and_contract():
    c = honest_contract()
    assert c["marker"] == MARKER == "WALL_HONEST_EMPTY_VS_DOWN"
    assert c["fetch_down_only"] is True
    assert c["paint_throw_not_down"] is True
    assert c["empty_not_down"] is True
    assert c["llm_empty_is_dash"] is True
    assert "restart" in c["recovery"].lower()
    assert c["empty_messages"]["session"] == "No desks are here. Ask your agent to join."


@pytest.mark.parametrize(
    "kwargs,expect",
    [
        ({"network_error": True}, "down"),
        ({"ok": False, "status": 502}, "down"),
        ({"ok": False, "status": 500, "content_type": "application/json"}, "down"),
        ({"ok": True, "status": 200, "content_type": "text/html"}, "down"),
        ({"ok": True, "status": 200, "content_type": "application/json", "body": {}}, "ok"),
        ({"ok": True, "status": 200, "content_type": "application/json", "body": {"agents": [], "kpis": []}}, "ok"),
        ({"status": 404}, "down"),
        ({"status": 200, "content_type": "application/json"}, "ok"),
    ],
)
def test_classify_fetch_table(kwargs, expect):
    assert classify_fetch(**kwargs) == expect


@pytest.mark.parametrize(
    "kwargs,expect",
    [
        ({"fetch": "down"}, "down"),
        ({"fetch": "ok", "paint_error": True}, "paint_error"),
        ({"fetch": "down", "paint_error": True}, "down"),
        ({"fetch": "ok", "payload": None}, "empty"),
        ({"fetch": "ok", "payload": {}}, "empty"),
        ({"fetch": "ok", "payload": {"agents": [], "kpis": [], "mailbox": [], "needs": []}}, "empty"),
        ({"fetch": "ok", "payload": {"agents": [{"alive": True, "owner": "builder"}], "kpis": []}}, "ok"),
        ({"fetch": "ok", "payload": {"agents": [], "kpis": [{"kpi": "x", "value": "1"}]}}, "ok"),
        ({"fetch": "ok", "paint_error": True, "payload": {"agents": [], "kpis": []}}, "paint_error"),
    ],
)
def test_classify_outcome_table(kwargs, expect):
    assert classify_outcome(**kwargs) == expect


@pytest.mark.parametrize(
    "tokens,est,expect",
    [
        (None, None, "\u2014"),
        ("", None, "\u2014"),
        (0, None, "0"),
        (12, 99, "12"),
        (None, 50, "50"),
    ],
)
def test_honest_llm_display(tokens, est, expect):
    assert honest_llm_display(tokens, est) == expect


@pytest.mark.parametrize(
    "mill_bytes,mill_rows,expect",
    [
        (0, 0, "\u2014"),
        (None, 0, "\u2014"),
        (0, 1, "0"),
        (9000, 2, "9000"),
    ],
)
def test_honest_mill_bytes_display(mill_bytes, mill_rows, expect):
    assert honest_mill_bytes_display(mill_bytes, mill_rows) == expect


def test_sum_llm_tokens_never_fakes_null():
    assert sum_llm_tokens([]) is None
    assert sum_llm_tokens([{"source": "mill", "tokens": None}]) is None
    assert sum_llm_tokens([{"source": "grok", "tokens": None}, {"source": "mill", "tokens": 99}]) is None
    assert sum_llm_tokens([{"source": "grok", "tokens": 3}, {"source": "grok", "tokens": 4}]) == 7.0


def test_score_pulse_empty_llm_is_none_not_zero():
    pulse = score_pulse_counts({"kpis": [], "spend": [], "spend_lines": []}, [], span="24h")
    assert pulse["tokens"] is None
    assert pulse["millBytes"] is None
    assert pulse.get("millRows", 0) == 0


def test_score_spend_pulse_mill_rows_key():
    sp = score_spend_pulse({"spend_lines": []}, span="24h")
    assert sp["tokens"] is None
    assert sp["millBytes"] is None
    assert sp["millRows"] == 0


def test_api_down_banner_mentions_desk_restart():
    html = api_down_banner_html()
    assert "mill API down" in html
    assert "restart" in html.lower()
    assert "empty" in html.lower()


def test_boot_and_lib_markers_shipped():
    boot = (default_pack_dir() / "boot.js").read_text(encoding="utf-8")
    data = (wall_ui_root() / "lib" / "data.js").read_text(encoding="utf-8")
    assert "WALL_HONEST_EMPTY_VS_DOWN" in boot
    assert "WALL_HONEST_EMPTY_VS_DOWN" in data
    assert "wallClassifyFetch" in data
    assert "clearApiDownBanner" in boot
    assert "wallPaintThrowSafe" in data
    assert "paintApiDown" in boot
    board = default_board_path().read_text(encoding="utf-8")
    assert "async function tick" not in board
