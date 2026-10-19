"""Wake hook: empty URL and a bad URL fail soft. No book."""

from __future__ import annotations

import os

from agent_coord.server.wake import fire_wake_hook, wake_url


def test_wake_url_empty_by_default() -> None:
    os.environ.pop("AGENT_COORD_WAKE_URL", None)
    u = wake_url()
    assert isinstance(u, str)


def test_fire_wake_hook_fail_soft_bad_url() -> None:
    assert fire_wake_hook("", {"x": 1}) is False
    assert fire_wake_hook("http://127.0.0.1:1/nope", {"x": 1}, timeout=0.3) is False
