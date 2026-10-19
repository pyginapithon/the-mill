"""records/activity.py (old mill presence wire)."""
from __future__ import annotations

import pytest

from agent_coord.server.records.activity import heartbeat_interval


@pytest.mark.parametrize(
    "lease_s, expect",
    [
        (0, 5.0),
        (3, 5.0),
        (15, 5.0),
        (15 * 60, 300.0),
        (60, 20.0),
        (9, 5.0),
        (18, 6.0),
    ],
)
def test_heartbeat_interval(lease_s, expect):
    assert heartbeat_interval(lease_s) == expect
