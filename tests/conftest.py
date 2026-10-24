"""Isolate mill_home so pytest never writes ~/.mill/session/*.token on this office."""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _isolate_mill_home(tmp_path_factory, monkeypatch):
    d = tmp_path_factory.mktemp("mill-home")
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(d))
    yield d



def pytest_terminal_summary(terminalreporter):
    """Temporary (#867 CI diagnosis): name failing tests in GitHub annotations."""
    import os

    if not os.environ.get("GITHUB_ACTIONS"):
        return
    for key in ("failed", "error"):
        for rep in terminalreporter.stats.get(key, []):
            text = str(getattr(rep, "longreprtext", "") or "")[-1500:]
            text = text.replace("%", "%25").replace("\r", "").replace("\n", "%0A")
            terminalreporter.write_line("::error title=pytest %s::%s%%0A%s" % (key, getattr(rep, "nodeid", "?"), text))
