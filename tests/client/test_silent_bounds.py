"""Hold resource and watcher hint refuse a silent cut (#143). Note bounds: test_note_detail_budget_360."""
from __future__ import annotations

import pytest

from agent_coord.helpers.bounds import (
    bound_watcher_hint,
    resource_name,
)
from agent_coord.helpers.errors import CoordError


def test_resource_rejects_empty_and_65():
    with pytest.raises(CoordError) as ei:
        resource_name("")
    assert str(ei.value) == "resource must be 1..64 characters"
    with pytest.raises(CoordError):
        resource_name("r" * 65)
    assert resource_name("r" * 64) == "r" * 64


def test_watcher_hint_refuses_past_4096():
    with pytest.raises(CoordError) as ei:
        bound_watcher_hint("h" * 4097)
    assert str(ei.value) == "watcher: hint would be 4097 chars (max 4096); shorten"
    assert bound_watcher_hint("ok") == "ok"
