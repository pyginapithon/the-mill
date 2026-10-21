"""#620 the welcome link (it carries the seat secret) never goes on argv.

mill join reads it from a file (--link-file PATH, the file mill invite writes)
or from stdin (--link-stdin). A link on the command line is refused with the
file form and never echoed. Row F69 (join-link-file).
"""
from __future__ import annotations

import base64
import io

import pytest

from agent_coord.__main__ import main

_PEM_B64 = base64.b64encode(b"-----BEGIN CERTIFICATE-----\nMIIBTESTCA\n-----END CERTIFICATE-----\n").decode("ascii")
SEAT = "seat-secret-0123456789"
WELCOME = f"https://office.example/welcome?desk=grok-tui&seat={SEAT}&project=the-mill&pem={_PEM_B64}"


@pytest.fixture(autouse=True)
def _env(monkeypatch, tmp_path):
    from agent_coord.client.offices import bind_cli_office

    bind_cli_office("")
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path / "home"))
    monkeypatch.setenv("AGENT_COORD_CONFIG", str(tmp_path / "home" / "config.toml"))
    monkeypatch.setattr("agent_coord.install.packver.checkout_dist_line", lambda: "")
    monkeypatch.setattr("agent_coord.client.offices.write_global_active", lambda name, **kw: tmp_path / "active")
    yield
    bind_cli_office("")


@pytest.fixture
def joined(monkeypatch):
    seen: dict = {}

    def fake(url, office, **kwargs):
        seen["url"], seen["office"] = url, office
        return {"ok": True, "desk": "grok-tui", "office": office}

    monkeypatch.setattr("agent_coord.client.offices.join_office", fake)
    return seen


@pytest.mark.parametrize("raw", [WELCOME, "'" + WELCOME + "'", "office.example/welcome?desk=d&seat=" + SEAT])
def test_a_link_on_argv_is_refused_and_never_echoed(joined, capsys, raw):
    rc = main(["join", raw])
    out = capsys.readouterr()
    assert rc == 2 and joined == {}
    assert "mill join --link-file PATH" in out.err and "--link-stdin" in out.err
    assert SEAT not in out.err + out.out and "welcome?" not in out.err + out.out


def test_link_file_joins(joined, tmp_path, capsys):
    f = tmp_path / "grok-tui.link"
    f.write_text("  '" + WELCOME + "'\r\n\n", encoding="utf-8")
    rc = main(["join", "--link-file", str(f)])
    assert rc == 0 and joined["url"] == WELCOME and joined["office"] == "office.example"
    assert SEAT not in capsys.readouterr().out


def test_link_stdin_joins(joined, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(WELCOME + "\n"))
    assert main(["join", "--link-stdin", "--office", "home"]) == 0
    assert joined["url"] == WELCOME and joined["office"] == "home"


def test_link_file_with_two_lines_is_refused(joined, tmp_path, capsys):
    f = tmp_path / "two.link"
    f.write_text(WELCOME + "\n" + WELCOME + "\n", encoding="utf-8")
    assert main(["join", "--link-file", str(f)]) == 2 and joined == {}
    err = capsys.readouterr().err
    assert "one line" in err and SEAT not in err


def test_missing_link_file_is_refused(joined, tmp_path, capsys):
    assert main(["join", "--link-file", str(tmp_path / "nope.link")]) == 2 and joined == {}
    assert "could not read the link file" in capsys.readouterr().err


def test_both_link_sources_are_refused(joined, tmp_path, monkeypatch, capsys):
    f = tmp_path / "a.link"
    f.write_text(WELCOME, encoding="utf-8")
    monkeypatch.setattr("sys.stdin", io.StringIO(WELCOME))
    assert main(["join", "--link-file", str(f), "--link-stdin"]) == 2 and joined == {}


def test_link_source_with_a_desk_name_is_refused(joined, tmp_path, capsys):
    f = tmp_path / "a.link"
    f.write_text(WELCOME, encoding="utf-8")
    assert main(["join", "grok-tui", "--link-file", str(f)]) == 2 and joined == {}
    assert "either" in capsys.readouterr().err


def test_bare_join_names_the_file_form(joined, capsys):
    assert main(["join"]) == 1
    assert "--link-file" in capsys.readouterr().err


def test_join_usage_shows_the_file_form(capsys):
    from agent_coord.__main__ import _build_parser

    with pytest.raises(SystemExit):
        _build_parser().parse_args(["join", "--help"])
    out = capsys.readouterr().out
    assert "usage: mill join --link-file PATH" in out


def test_mint_seat_has_no_argv_join_form(monkeypatch):
    from agent_coord.server.admin import seats as seats_mod

    monkeypatch.setattr("agent_coord.server.records.join.upsert", lambda *a, **k: [{"owner": "bot-z", "desk_id": 1}])
    monkeypatch.setattr("agent_coord.server.records.member.put_office", lambda *a, **k: None)
    monkeypatch.setattr(seats_mod, "_mill_ca_pem", lambda: "-----BEGIN CERTIFICATE-----\nX\n-----END CERTIFICATE-----\n")
    row = seats_mod.mint_seat(object(), desk="bot-z", project="ops", created_by="admin", mill_url="https://wall.example")
    assert "join_argv" not in row
    assert not hasattr(seats_mod, "cold_join_argv")
