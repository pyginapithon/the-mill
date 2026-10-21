"""mill join success prints the next connect line (#249 / #253)."""
from __future__ import annotations

import base64
from urllib.parse import parse_qs, urlencode, urlparse

from agent_coord.__main__ import main
from agent_coord.client.offices import join_office, next_connect_line, project_on_url, read_seat_project

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



def _welcome(host: str, desk: str, seat: str, project: str = "", pem: str = _PEM) -> str:
    fields = {
        "desk": desk,
        "seat": seat,
        "pem": base64.b64encode(pem.encode("utf-8")).decode("ascii"),
    }
    if project:
        fields["project"] = project
    return f"https://{host}/welcome?" + urlencode(fields)


def test_next_connect_line_shapes() -> None:
    assert next_connect_line("office-a", "the-mill", "build-app") == (
        "next: bash -c 'mill --office office-a connect build-app >/dev/null 2>&1 & trap \"kill $!\" EXIT; mill --office office-a inbox'"
    )
    assert next_connect_line("", "the-mill", "build-app") == "next: bash -c 'mill connect build-app >/dev/null 2>&1 & trap \"kill $!\" EXIT; mill inbox'"
    assert next_connect_line("office-a", "", "build-app") == "next: bash -c 'mill --office office-a connect build-app >/dev/null 2>&1 & trap \"kill $!\" EXIT; mill --office office-a inbox'"
    assert next_connect_line("office-a", "the-mill", "") == ""


def test_project_on_url_reads_query_only() -> None:
    assert project_on_url("https://wall.example/welcome?desk=build-app&project=the-mill") == "the-mill"
    assert project_on_url("https://wall.example/") == ""


def test_join_office_writes_seat_roster_and_next(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    row = join_office(
        _welcome("203.0.113.10", "build-app", "sek", "the-mill"),
        "office-a",
        dest=tmp_path,
    )
    assert row["ok"] is True
    assert row["project"] == "the-mill"
    assert row["next"] == "next: bash -c 'mill --office office-a connect build-app >/dev/null 2>&1 & trap \"kill $!\" EXIT; mill --office office-a inbox'"
    assert read_seat_project("build-app", host="203.0.113.10", dest=tmp_path) == "the-mill"


def test_join_office_next_names_only_the_desk(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    monkeypatch.setattr(
        "agent_coord.client.http.mill_http_call",
        lambda body: {"token": "sek", "owner": "build-app", "group_id": "Office"},
    )
    row = join_office(
        _welcome("203.0.113.10", "build-app", "sek"),
        "office-a",
        dest=tmp_path,
    )
    assert row["ok"] is True
    assert row["next"] == "next: bash -c 'mill --office office-a connect build-app >/dev/null 2>&1 & trap \"kill $!\" EXIT; mill --office office-a inbox'"
    assert read_seat_project("build-app", host="203.0.113.10", dest=tmp_path) == ""


def test_join_success_prints_the_next_line(monkeypatch, tmp_path, capsys) -> None:
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    monkeypatch.setattr("agent_coord.install.packver.checkout_dist_line", lambda: "")
    line = "next: bash -c 'mill --office office-a connect build-app >/dev/null 2>&1 & trap \"kill $!\" EXIT; mill --office office-a inbox'"
    link = _welcome("office.example", "build-app", "sek", "the-mill")

    def fake(url, office, **kwargs):
        return {"ok": True, "desk": "build-app", "project": "the-mill", "next": line}

    monkeypatch.setattr("agent_coord.client.offices.join_office", fake)
    lf = tmp_path.parent / "build-app.link"
    lf.write_text(link, encoding="utf-8")
    rc = main(["join", "--office", "office-a", "--link-file", str(lf)])
    out = capsys.readouterr().out
    assert rc == 0
    assert line in [ln.strip() for ln in out.splitlines()]


def test_join_office_stores_seat_roster_from_link(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    row = join_office(
        _welcome("203.0.113.10", "build-app", "sekrit", "the-mill"),
        "office-a",
        dest=tmp_path,
    )
    assert row["ok"] is True
    assert row["next"] == "next: bash -c 'mill --office office-a connect build-app >/dev/null 2>&1 & trap \"kill $!\" EXIT; mill --office office-a inbox'"
    assert read_seat_project("build-app", host="203.0.113.10", dest=tmp_path) == "the-mill"


def test_mint_invite_url_includes_seat_roster(monkeypatch) -> None:
    from agent_coord.server.admin import seats as seats_mod

    def fake_upsert(cn, project, desk, role="", token_hash=None, doing=None):
        return [{"owner": desk, "desk_id": 1}]

    monkeypatch.setattr("agent_coord.server.records.join.upsert", fake_upsert)
    monkeypatch.setattr("agent_coord.server.records.member.put_office", lambda *a, **k: None)
    row = seats_mod.mint_seat(
        object(),
        desk="bot-z",
        created_by="admin",
        mill_url="https://wall.example",
    )
    q = parse_qs(urlparse(row["invite_url"]).query)
    assert q["desk"] == ["bot-z"]
    assert q["project"] == ["the-mill"]
    assert row["project"] == "the-mill"
    assert "/welcome?" in row["invite_url"]


def test_join_office_refuses_invite_key(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    row = join_office(
        "https://203.0.113.10/?invite=KEY123",
        "office-a",
        dest=tmp_path,
    )
    assert row["ok"] is False
    assert "invite-key" in row["error"]


def test_join_office_refuses_bare_path(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    row = join_office("https://203.0.113.10/", "office-a", dest=tmp_path)
    assert row["ok"] is False
    assert "welcome" in row["error"]


def test_join_office_wall_seat_roster_when_link_omits_project(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    monkeypatch.setattr(
        "agent_coord.client.http.mill_http_call",
        lambda body: {"token": "sek", "owner": "build-app", "group_id": "the-mill"},
    )
    row = join_office(
        _welcome("203.0.113.10", "build-app", "sek"),
        "office-a",
        dest=tmp_path,
    )
    assert row["ok"] is True
    assert row["project"] == "the-mill"
    assert row["next"] == "next: bash -c 'mill --office office-a connect build-app >/dev/null 2>&1 & trap \"kill $!\" EXIT; mill --office office-a inbox'"
    assert read_seat_project("build-app", host="203.0.113.10", dest=tmp_path) == "the-mill"


def test_mint_seat_link_carries_project(monkeypatch) -> None:
    from agent_coord.server.admin import seats as seats_mod

    def fake_upsert(cn, project, desk, role="", token_hash=None, doing=None):
        return [{"owner": desk, "desk_id": 1}]

    monkeypatch.setattr("agent_coord.server.records.join.upsert", fake_upsert)
    monkeypatch.setattr("agent_coord.server.records.member.put_office", lambda *a, **k: None)
    monkeypatch.setattr(seats_mod, "_mill_ca_pem", lambda: _PEM)
    row = seats_mod.mint_seat(
        object(),
        desk="bot-z",
        project="ops",
        created_by="admin",
        mill_url="https://wall.example",
    )
    q = parse_qs(urlparse(row["invite_url"]).query)
    assert q["project"] == ["ops"]
    assert row["project"] == "ops"
    assert "join_argv" not in row  # #620: the link is never argv
