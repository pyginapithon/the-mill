"""Server unit tests use a mock connection. The live-project check (#237) needs
the name table, so it is a no-op here unless the test is marked sql."""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _live_project_noop_without_sql(request, monkeypatch):
    if request.node.get_closest_marker("sql") is not None:
        return
    monkeypatch.setattr(
        "agent_coord.server.api.mill.rpc._require_live_project",
        lambda cn, project, command: str(project or "").strip(),
    )
