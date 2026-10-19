"""Isolate mill_home so pytest never writes ~/.mill/session/*.token on this office."""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _isolate_mill_home(tmp_path_factory, monkeypatch):
    d = tmp_path_factory.mktemp("mill-home")
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(d))
    yield d
