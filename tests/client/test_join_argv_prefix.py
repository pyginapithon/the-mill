"""Passing join_argv to `mill join` must not see a second mill join (#150)."""
from __future__ import annotations

import base64

from agent_coord.__main__ import main, strip_doubled_join_prefix

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



def test_strip_keeps_the_link_after_the_repeated_prefix():
    got = strip_doubled_join_prefix(
        [
            "join",
            "mill",
            "join",
            _WELCOME,
        ]
    )
    assert got == ["join", _WELCOME]


def test_strip_leaves_a_normal_join_alone():
    raw = ["join", "--office", "home", _WELCOME]
    assert strip_doubled_join_prefix(raw) == raw


def test_doubled_prefix_reaches_join(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    seen = {}

    def fake(url, office, **kwargs):
        seen["url"] = url
        seen["office"] = office
        return {
            "ok": True,
            "office": office,
            "desk": "grok-tui",
            "project": "the-mill",
            "next": "next: bash -c 'mill --office home connect grok-tui >/dev/null 2>&1 & trap \"kill $!\" EXIT; mill --office home inbox'",
        }

    monkeypatch.setattr("agent_coord.client.offices.join_office", fake)
    rc = main(
        [
            "join",
            "mill",
            "join",
            "--office",
            "home",
            _WELCOME,
        ]
    )
    err = capsys.readouterr().err
    assert rc == 0
    assert seen["url"] == _WELCOME
    assert seen["office"] == "home"
    assert "unrecognized arguments" not in err


def test_join_join_url_exits_1_on_stderr(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))

    def fake(*_a, **_k):
        raise AssertionError("join")

    monkeypatch.setattr("agent_coord.client.offices.join_office", fake)
    # link positional is "join"; handler refuses the doubled word (#157).
    rc = main(["join", "join", "--office", "home"])
    out = capsys.readouterr()
    assert rc == 1
    assert out.out.strip() == ""
    assert "extra join word" in out.err
    assert list(tmp_path.iterdir()) == []


def test_join_failure_json_is_stderr_exit_1(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))

    def fake(*_a, **_k):
        return {"ok": False, "error": "wall unreachable"}

    monkeypatch.setattr("agent_coord.client.offices.join_office", fake)
    rc = main(["join", "--office", "home", _WELCOME])
    out = capsys.readouterr()
    assert rc == 1
    assert out.out.strip() == ""
    assert "wall unreachable" in out.err
