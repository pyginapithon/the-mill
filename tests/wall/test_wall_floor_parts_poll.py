# -*- coding: utf-8 -*-
"""Wall floor poll: tab-scoped parts + coalesced tick (no fat stripNeed)."""
from __future__ import annotations

import re
from pathlib import Path

from agent_coord.web.wall_logic.packs import wall_ui_root

BOOT = wall_ui_root() / "default" / "boot.js"


def _boot() -> str:
    return BOOT.read_text(encoding="utf-8")


def test_wall_parts_no_strip_need_fat_concat():
    """Open tab must not re-append agents+mail+scores+todos on every poll."""
    src = _boot()
    assert "function wallParts()" in src
    assert "stripNeed" not in src
    # MAIL Rooms vs board default (session)
    assert 'mailView === "rooms") ? "mail,trees" : "mail"' in src
    assert 'core = "todos,trees"' in src
    assert 'core = "scores"' in src
    # session default returns agents only (not mail/scores/todos)
    m = re.search(
        r"function wallParts\(\) \{(?P<body>.*?)\n    \}\n",
        src,
        flags=re.S,
    )
    assert m, "wallParts body not found"
    body = m.group("body")
    assert "return core;" in body
    assert '["agents", "mail", "scores", "todos"]' not in body


def test_tick_coalesce_single_flight_and_one_interval():
    src = _boot()
    assert "TICK_DEBOUNCE_MS" in src
    assert "_tickInflight" in src
    assert "_tickAgain" in src
    assert "async function _tickBody()" in src
    assert "function tick(" in src  # tick() or tick(force) Wave 2
    # single named interval; clear before set
    assert "__wallFloorPoll" in src
    assert "clearInterval(window.__wallFloorPoll)" in src
    assert "15000" in src
    intervals = [
        m.start()
        for m in re.finditer(
            r"setInterval\(\s*(?:tick|function\s*\(\)\s*\{\s*tick\(\);\s*\})\s*,\s*15000\s*\)",
            src,
        )
    ]
    assert len(intervals) == 1


def test_card_list_paint_gated_on_slice_parts():
    """Poll without todos/scores must not re-bind every card body into the DOM."""
    src = _boot()
    # partPaint = sliceHas && !fpHits (Loop-3 fingerprint empty-on-match skip)
    assert "partPaint" in src
    assert 'partPaint("todos") || partPaint("trees")' in src
    assert 'partPaint("scores")' in src
    assert 'partPaint("mail")' in src
    # board/cards calls stay behind the gate (Wave 2 may await wallEnsureDomain in between)
    assert re.search(
        r'if \(partPaint\("todos"\) \|\| partPaint\("trees"\)\) \{.*?safe\(function \(\) \{ board\(d\); \}, "jobs"\);',
        src,
        flags=re.S,
    )
    assert re.search(
        r'if \(partPaint\("scores"\)\) safe\(function \(\) \{ cards\(d\); \}, "scorecards"\);',
        src,
    )


def test_expected_parts_query_strings_documented_in_boot():
    """Poll parts become versioned routes. Timeline still passes parts=."""
    src = _boot()
    assert '"mail,trees"' in src
    assert "function wallV1Routes" in src
    assert '"/api/v1/rooms"' in src
    assert '"/api/v1/mailbox"' in src
    assert "&parts=" in src


def test_tick_reuses_fresh_rail_read():
    """The restore tick and the pick tick it starts read /api/pov once, not twice."""
    src = _boot()
    assert "const WALL_RAIL_FRESH_MS = 5000;" in src
    assert "_railBookAt = Date.now();" in src
    assert "if (Date.now() - _railBookAt > WALL_RAIL_FRESH_MS) loadRailBook();" in src


def test_clock_never_bare_utc():
    """Every clock paint keeps version, node and the local zone (wallClockLine)."""
    src = _boot()
    assert "toISOString().slice(11, 19)" not in src
    assert src.count("textContent = wallClockLine(") >= 4
