"""#253 join: one door, link only - edge cases."""
from __future__ import annotations

import base64
from urllib.parse import parse_qs, urlencode, urlparse

from agent_coord.__main__ import main
from agent_coord.client.offices import is_invite_key_link, is_welcome_link, join_office
from agent_coord.server.admin import seats as seats_mod

_PEM = (
    "-----BEGIN CERTIFICATE-----\n"
    "MIIBTESTCA\n"
    "-----END CERTIFICATE-----\n"
)



import pytest


@pytest.fixture(autouse=True)
def _clear_cli_office():
    from agent_coord.client.offices import bind_cli_office

    bind_cli_office("")
    yield
    bind_cli_office("")



def _welcome(host, desk, seat, project="the-mill", pem=_PEM, extra=None):
    fields = {
        "desk": desk,
        "seat": seat,
        "pem": base64.b64encode(pem.encode("utf-8")).decode("ascii"),
    }
    if project:
        fields["project"] = project
    if extra:
        fields.update(extra)
    return f"https://{host}/welcome?" + urlencode(fields)


def test_is_welcome_link_requires_desk_seat_and_path():
    assert is_welcome_link(_welcome("w.example", "d", "s"))
    assert not is_welcome_link("https://w.example/?invite=KEY")
    assert not is_welcome_link("https://w.example/")
    assert not is_welcome_link("https://w.example/welcome?desk=d")  # no seat
    assert not is_welcome_link("https://w.example/other?desk=d&seat=s")


def test_is_invite_key_link_excludes_welcome():
    assert is_invite_key_link("https://w.example/?invite=KEY")
    assert not is_invite_key_link(_welcome("w.example", "d", "s"))


def test_join_refuses_old_cli_flags(monkeypatch, tmp_path, capsys):
    import pytest

    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    monkeypatch.setattr("agent_coord.install.packver.checkout_dist_line", lambda: "")
    with pytest.raises(SystemExit) as ei:
        main(
            [
                "join",
                "--office",
                "home",
                "--url",
                "https://office.example/",
                "--desk",
                "bot",
                "--seat",
                "sek",
                "--ca",
                "QQ==",
            ]
        )
    assert ei.value.code == 2
    err = capsys.readouterr().err
    assert "unrecognized arguments" in err.lower()
    for flag in ("--url", "--desk", "--seat", "--ca"):
        assert flag in err


def test_join_refuses_missing_pem(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    # welcome without pem=
    url = "https://203.0.113.10/welcome?" + urlencode({"desk": "bot", "seat": "sek", "project": "the-mill"})
    row = join_office(url, "home", dest=tmp_path)
    assert row["ok"] is False
    assert "pem" in row["error"]


def test_join_refuses_bad_pem(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    url = "https://203.0.113.10/welcome?" + urlencode(
        {"desk": "bot", "seat": "sek", "pem": base64.b64encode(b"not-a-cert").decode()}
    )
    row = join_office(url, "home", dest=tmp_path)
    assert row["ok"] is False
    assert "pem" in row["error"].lower() or "CA" in row["error"] or "welcome" in row["error"]


def test_invite_url_for_embeds_pem():
    url = seats_mod.invite_url_for(
        desk="bot",
        seat="sek",
        base="https://wall.example",
        project="ops",
        ca_pem=_PEM,
    )
    assert "/welcome?" in url
    q = parse_qs(urlparse(url).query)
    assert q["desk"] == ["bot"]
    assert q["seat"] == ["sek"]
    assert q["project"] == ["ops"]
    assert base64.b64decode(q["pem"][0]).decode("utf-8") == _PEM


def test_cold_join_argv_empty_without_pem():
    assert seats_mod.cold_join_argv(
        origin="https://wall.example",
        desk="bot",
        seat="sek",
        ca_pem="",
        project="ops",
    ) == []
