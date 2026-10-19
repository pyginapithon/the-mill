"""claimed + progress-done is mill pass, not auto-close."""
from __future__ import annotations

from agent_coord.server.records.todo import progress_is_done, next_status


def test_progress_is_done_100() -> None:
    assert progress_is_done("100%") is True
    assert progress_is_done("3/3") is True
    assert progress_is_done("done") is True
    assert progress_is_done("ship done") is True
    assert progress_is_done("implementing") is False
    assert progress_is_done("describe") is False
    assert progress_is_done("") is False
    assert progress_is_done("1/3") is False


def test_next_status_does_not_auto_done() -> None:
    assert next_status("claimed", "100%") == "shipped"
    assert next_status("claimed", "implementing") == "claimed"
    assert next_status("shipped", "100%") == "shipped"
