"""records/todo.py helpers (status/progress)."""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from agent_coord.server.records.todo import format_progress, parse_eta


@pytest.mark.parametrize(
    "kwargs, expect",
    [
        ({}, ""),
        ({"text": "shipped"}, "shipped"),
        ({"n": 1, "of": 4}, "1/4"),
        ({"n": 3}, "3"),
        ({"pct": 75}, "75%"),
        ({"n": 1, "of": 4, "note": "leased"}, "1/4 leased"),
        ({"text": "x", "note": "y"}, "x y"),
        ({"text": "  " + ("z" * 80), "note": "tail"}, ("z" * 80 + " tail")[:64]),
    ],
)
def test_format_progress_table(kwargs, expect):
    assert format_progress(**kwargs) == expect


@pytest.mark.parametrize(
    "raw, delta_s",
    [
        ("20m", 20 * 60),
        ("2h", 2 * 3600),
        ("90s", 90),
        ("1d", 86400),
        (" 3M ", 3 * 60),
    ],
)
def test_parse_eta_spans(raw, delta_s):
    now = datetime(2026, 9, 10, 12, 0, 0)
    got = parse_eta(raw, now)
    assert got == now + timedelta(seconds=delta_s)


@pytest.mark.parametrize("raw", [None, "", "   "])
def test_parse_eta_empty(raw):
    assert parse_eta(raw) is None


def test_parse_eta_absolute():
    now = datetime(2026, 9, 10, 12, 0, 0)
    assert parse_eta("2026-09-11 00:30", now) == datetime(2026, 9, 11, 0, 30)
    assert parse_eta("2026-09-11T00:30:00Z", now) == datetime(2026, 9, 11, 0, 30)


@pytest.mark.parametrize("bad", ["0m", "bogus", "20x", "-1h"])
def test_parse_eta_rejects(bad):
    with pytest.raises(ValueError):
        parse_eta(bad, datetime(2026, 9, 10, 12, 0, 0))

