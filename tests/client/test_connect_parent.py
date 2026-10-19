"""mill connect stops once the process that launched it is gone (#192)."""
from __future__ import annotations

from agent_coord.lib.proc import parent_gone


def test_parent_gone_when_lookup_misses():
    assert parent_gone(42, lookup=lambda _pid: None) is True


def test_parent_stays_when_lookup_finds_it():
    assert parent_gone(42, lookup=lambda _pid: 0) is False
    assert parent_gone(42, lookup=lambda _pid: 9) is False


def test_unknown_parent_does_not_stop_connect():
    assert parent_gone(0, lookup=lambda _pid: None) is False
    assert parent_gone(None, lookup=lambda _pid: None) is False
