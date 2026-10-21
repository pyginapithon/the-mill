# -*- coding: utf-8 -*-
"""#281: a seatless mill connect NAME gets one plain refusal, no lookup.

A roster, an unknown name and a desk without a seat on this computer all get
the same line and exit 2; nothing is printed as connecting and no request
leaves the computer. A desk with a seat still connects. Regression row F30
(connect-seatless).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from agent_coord.__main__ import main, seatless_connect_line


@pytest.fixture
def office(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    monkeypatch.setattr("agent_coord.install.packver.checkout_dist_line", lambda: "")
    monkeypatch.setattr("agent_coord.client.http.mill_url", lambda: "https://office.example", raising=False)
    monkeypatch.setattr("agent_coord.__main__.mill_url", lambda: "https://office.example", raising=False)
    seats = {"builder": "tok-" + "b" * 8}
    monkeypatch.setattr("agent_coord.client.tokens.read_session_token", lambda who: seats.get(who, ""))
    called = []
    monkeypatch.setattr("agent_coord.client.http.mill_here_over_http", lambda a: called.append(a) or 0)
    sent = []

    def no_network(*a, **k):
        sent.append(a)
        raise AssertionError("seatless connect must not call the office")

    monkeypatch.setattr("agent_coord.client.http.mill_http_call", no_network, raising=False)
    return called, sent


@pytest.mark.parametrize(
    "argv,who",
    [
        (["connect", "cold-test"], "cold-test"),
        (["connect", "zz-unknown-281"], "zz-unknown-281"),
        (["connect", "the-mill", "nobody-here"], "nobody-here"),
        (["connect", "Cold-Test"], "Cold-Test"),
    ],
)
def test_seatless_connect_is_one_line_exit_2(office, capsys, argv, who):
    called, sent = office
    rc = main(argv)
    cap = capsys.readouterr()
    assert rc == 2 and not called and not sent
    from agent_coord.helpers.ident import desk_name

    lines = cap.err.strip().splitlines()
    assert lines == [seatless_connect_line(desk_name(who))]
    assert "connecting" not in cap.err and cap.out == ""


def test_roster_and_unknown_name_read_the_same(office, capsys):
    main(["connect", "cold-test"])
    a = capsys.readouterr().err.replace("cold-test", "NAME")
    main(["connect", "zz-unknown-281"])
    b = capsys.readouterr().err.replace("zz-unknown-281", "NAME")
    assert a == b


def test_line_names_join_and_connected_without_a_lookup():
    line = seatless_connect_line("x1")
    assert "mill join --link-file PATH" in line
    assert "mill connected ROSTER" in line
    assert "\n" not in line and line.isascii()


def test_desk_with_a_seat_still_connects(office, capsys):
    called, _ = office
    rc = main(["connect", "builder"])
    assert rc == 0 and len(called) == 1
    assert "connecting" in capsys.readouterr().err


def test_empty_desk_still_desk_required(office, capsys):
    called, _ = office
    rc = main(["connect", ""])
    assert rc != 0 and not called


def test_docs_name_the_row():
    root = Path(__file__).resolve().parents[2]
    text = (root / "docs" / "protocol" / "connect.md").read_text(encoding="utf-8")
    assert "Regression row F30 (connect-seatless)" in text
