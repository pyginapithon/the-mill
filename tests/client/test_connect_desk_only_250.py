"""mill connect with only a desk joins the Office roster; a named roster overrides it (#250, 0.7.x)."""
from __future__ import annotations

import json

import pytest

from agent_coord.__main__ import _build_parser, main
from agent_coord.client.offices import bind_cli_host, bind_cli_office, desk_token_path, write_alias


@pytest.fixture(autouse=True)
def _reset_connect_cli_binding():
    """bind_cli_host is process-global. Do not leak a host into later tests."""
    yield
    bind_cli_host("")
    bind_cli_office("")


def _wall(monkeypatch, tmp_path, url="https://203.0.113.10"):
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    monkeypatch.setattr("agent_coord.install.packver.checkout_dist_line", lambda: "")
    monkeypatch.setattr("agent_coord.config.clear_shared_node_if_owner", lambda owner, dest=None: False)
    monkeypatch.setattr("agent_coord.client.http.mill_url", lambda: url)
    # A seat is present: #281 refuses a seatless connect before routing.
    monkeypatch.setattr("agent_coord.client.tokens.read_session_token", lambda who: "seat-" + who)
    seen: dict = {}

    def fake(args):
        seen["project"] = args.project
        seen["desk"] = args.desk
        seen["called"] = True
        return 0

    monkeypatch.setattr("agent_coord.client.http.mill_here_over_http", fake)
    write_alias("office-a", "203.0.113.10", dest=tmp_path)
    return seen


def _seat_roster(tmp_path, desk="build-app", project="the-mill") -> None:
    path = desk_token_path("203.0.113.10", desk, dest=tmp_path).with_name("project")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(project + "\n", encoding="utf-8")


def test_parser_does_not_default_project_to_the_mill() -> None:
    args = _build_parser().parse_args(["connect"])
    assert args.project == ""
    assert args.desk == ""
    one = _build_parser().parse_args(["connect", "build-app"])
    assert one.project == "build-app"
    assert one.desk == ""


def test_one_desk_uses_office_even_with_a_seat_roster(monkeypatch, tmp_path) -> None:
    """0.7.x decision: no roster named = the Office roster; the seat file is not read."""
    seen = _wall(monkeypatch, tmp_path)
    _seat_roster(tmp_path)
    rc = main(["--office", "office-a", "connect", "build-app"])
    assert rc == 0
    assert seen["desk"] == "build-app"
    assert seen["project"] == "Office"


def test_one_desk_without_seat_roster_uses_office(monkeypatch, tmp_path) -> None:
    seen = _wall(monkeypatch, tmp_path)
    rc = main(["--office", "office-a", "connect", "build-app"])
    assert rc == 0
    assert seen["project"] == "Office"


def test_the_mill_alone_is_a_desk_not_a_default_project(monkeypatch, tmp_path) -> None:
    seen = _wall(monkeypatch, tmp_path)
    rc = main(["--office", "office-a", "connect", "the-mill"])
    assert rc == 0
    assert seen["desk"] == "the-mill"
    assert seen["project"] == "Office"


def test_zero_positionals_still_need_a_desk(monkeypatch, tmp_path, capsys) -> None:
    seen = _wall(monkeypatch, tmp_path)
    rc = main(["--office", "office-a", "connect"])
    out = capsys.readouterr().out
    assert rc == 1
    assert seen == {}
    assert json.loads(out) == {"ok": False, "error": "mill connect: desk required", "desk": ""}


def test_host_shaped_positional_is_not_a_desk(monkeypatch, tmp_path, capsys) -> None:
    seen = _wall(monkeypatch, tmp_path)
    rc = main(["--office", "office-a", "connect", "office.example"])
    err = capsys.readouterr().err
    # #254: a host-shaped word is refused up front; the wall is the --office.
    assert rc == 2
    assert seen == {}
    assert "looks like a host" in err


def test_two_positionals_skip_the_seat_file(monkeypatch, tmp_path) -> None:
    seen = _wall(monkeypatch, tmp_path)
    rc = main(["--office", "office-a", "connect", "the-mill", "build-app"])
    assert rc == 0
    assert seen["project"] == "the-mill"
    assert seen["desk"] == "build-app"


def test_no_wall_still_says_join_first(monkeypatch, tmp_path, capsys) -> None:
    _wall(monkeypatch, tmp_path, url="")
    rc = main(["connect", "build-app"])
    err = capsys.readouterr().err
    assert rc == 1
    assert err.startswith("mill join https://<wall>/ first")
