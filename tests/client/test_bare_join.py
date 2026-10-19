"""A bare mill join refuses and writes nothing (#151 / #253)."""
from __future__ import annotations

import base64

from agent_coord.__main__ import main

_PEM = (
    "-----BEGIN CERTIFICATE-----\n"
    "MIIBTESTCA\n"
    "-----END CERTIFICATE-----\n"
)
_PEM_B64 = base64.b64encode(_PEM.encode("utf-8")).decode("ascii")
_WELCOME = (
    "https://office.example/welcome?desk=grok-tui&seat=abc&project=the-mill&pem="
    + _PEM_B64
)



import pytest


@pytest.fixture(autouse=True)
def _clear_cli_office():
    from agent_coord.client.offices import bind_cli_office

    bind_cli_office("")
    yield
    bind_cli_office("")



def test_bare_join_prints_usage_and_writes_nothing(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    monkeypatch.setenv("AGENT_COORD_CONFIG", str(tmp_path / "config.toml"))
    monkeypatch.setattr("agent_coord.install.packver.checkout_dist_line", lambda: "")
    rc = main(["join"])
    err = capsys.readouterr().err
    assert rc == 1
    assert "welcome" in err.lower() or "--office" in err
    assert "usage:" in err.lower()
    assert list(tmp_path.iterdir()) == []


def test_join_without_office_uses_the_link_host(monkeypatch, tmp_path, capsys):
    """ux7 regression: mill join <link> needs no --office (alias = link host)."""
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    monkeypatch.setattr("agent_coord.install.packver.checkout_dist_line", lambda: "")
    seen = {}

    def fake(url, office, **kwargs):
        seen["office"] = office
        return {"ok": True, "desk": "grok-tui", "office": office}

    monkeypatch.setattr("agent_coord.client.offices.join_office", fake)
    # The fake join writes no alias; the default-office save stands in as done (#274 reports a failed one).
    monkeypatch.setattr("agent_coord.client.offices.write_global_active", lambda name, **kw: tmp_path / "active")
    rc = main(["join", _WELCOME])
    assert rc == 0
    assert seen["office"]
    assert "--office" not in capsys.readouterr().err


def test_join_with_welcome_link_runs(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    seen = {}

    def fake(url, office, **kwargs):
        seen["url"] = url
        seen["office"] = office
        return {"ok": True, "desk": "grok-tui", "office": office}

    monkeypatch.setattr("agent_coord.client.offices.join_office", fake)
    rc = main(["join", "--office", "home", _WELCOME])
    assert rc == 0
    assert seen["url"] == _WELCOME
    assert seen["office"] == "home"
    capsys.readouterr()
