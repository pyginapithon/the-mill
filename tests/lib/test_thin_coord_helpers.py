"""wake hook leftovers (align/kpi deleted)."""
from __future__ import annotations

import re

from agent_coord.server import wake as wake_pkg
from agent_coord.server.wake import fire_wake_hook, wake_url
from agent_coord.lib.observe import FIXTURE_RE


def test_wake_url_empty(monkeypatch):
    monkeypatch.delenv("AGENT_COORD_WAKE_URL", raising=False)
    assert isinstance(wake_url(), str)
    assert isinstance(wake_pkg.wake_url(), str)


def test_fire_wake_hook_empty_url():
    assert fire_wake_hook("", {"a": 1}) is False
    assert fire_wake_hook("   ", {}) is False
    assert wake_pkg.fire_wake_hook("", {}) is False


def test_fixture_re():
    assert re.match(FIXTURE_RE, "t-deadbeef")
    assert not re.match(FIXTURE_RE, "mill")
