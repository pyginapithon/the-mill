"""Note, hold resource, and watcher hint refuse a silent cut (#143)."""
from __future__ import annotations

import pytest

from agent_coord.helpers.bounds import (
    append_note_detail,
    bound_watcher_hint,
    resource_name,
)
from agent_coord.helpers.errors import CoordError


def test_note_append_refuses_past_4096():
    prev = "a" * 4000
    with pytest.raises(CoordError) as ei:
        append_note_detail(prev, "b" * 200, replace=False)
    assert str(ei.value) == (
        "note: detail would be 4201 chars (max 4096); use --replace or shorten"
    )


def test_note_replace_still_refuses_an_overlong_note():
    with pytest.raises(CoordError) as ei:
        append_note_detail("old", "c" * 4097, replace=True)
    assert "4097" in str(ei.value)
    assert "--replace or shorten" in str(ei.value)


def test_note_append_keeps_both_when_it_fits():
    assert append_note_detail("old", "new", replace=False) == "old\nnew"


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
