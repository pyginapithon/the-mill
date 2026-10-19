"""JOB and PLAN share one status enum. upcoming is open."""
from __future__ import annotations

from agent_coord.server.records.todo import STATUSES as CARD_STATUSES, normalize_status, require_status


def test_upcoming_is_open() -> None:
    assert normalize_status("upcoming") == "open"
    assert normalize_status("doing") == "open"
    assert normalize_status("todo") == "parked"


def test_card_statuses() -> None:
    assert CARD_STATUSES == ("parked", "open", "claimed", "shipped", "done")
    for st in CARD_STATUSES:
        assert require_status(st) == st


def test_bad_status_raises() -> None:
    try:
        require_status("upcoming-typo")
        raise AssertionError("must raise")
    except ValueError:
        pass
