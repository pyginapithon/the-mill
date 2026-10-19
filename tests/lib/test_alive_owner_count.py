"""Plan #35: SESSION/FLOOR live_agents is unique alive owners."""
from __future__ import annotations

from agent_coord.lib.observe import alive_owner_count, snapshot


def test_two_pids_same_owner_count_once() -> None:
    agents = [
        {"owner": "build-assist", "alive": True, "pid": 1},
        {"owner": "build-assist", "alive": True, "pid": 2},
        {"owner": "build-presence", "alive": True, "pid": 3},
        {"owner": "dead", "alive": False, "pid": 4},
    ]
    assert alive_owner_count(agents) == 2


def test_snapshot_live_agents_dedups_owners() -> None:
    floor = {
        "projects": ["the-mill"],
        "locks": [],
        "agents": [
            {"owner": "build-assist", "alive": True},
            {"owner": "build-assist", "alive": True},
            {"owner": "builder", "alive": True},
        ],
        "events": [],
        "mailbox": [],
        "kpis": [],
        "needs": [],
        "issues": [],
    }
    out = snapshot(floor)
    assert out["live_agents"] == 2
