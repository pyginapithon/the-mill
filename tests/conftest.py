"""Isolate mill_home so pytest never writes ~/.mill/session/*.token on this office."""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _isolate_mill_home(tmp_path_factory, monkeypatch):
    d = tmp_path_factory.mktemp("mill-home")
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(d))
    yield d


def pytest_runtest_logreport(report):
    """Temporary (#867 CI diagnosis): name failing tests in a GitHub annotation."""
    import os

    if not os.environ.get("GITHUB_ACTIONS") or not report.failed:
        return
    text = str(report.longreprtext or "")[-1500:]
    text = text.replace("%", "%25").replace("\r", "").replace("\n", "%0A")
    print("\n::error title=%s %s::%s" % (report.when, report.nodeid, text), flush=True)
