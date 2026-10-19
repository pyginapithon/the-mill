# -*- coding: utf-8 -*-
"""Throwaway: mill send/reply CLI public shape (no live SQL)."""
from __future__ import annotations

import json
from unittest.mock import patch

import pytest

import os

from agent_coord.client.outbound.addressing import parse_mail_to_cli_json
from agent_coord.client.ws import write_rpc_bridge
from agent_coord.helpers.errors import CoordError


def _active(monkeypatch, tmp_path, desk: str) -> None:
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    monkeypatch.delenv("AGENT_COORD_OWNER", raising=False)
    write_rpc_bridge(desk, port=9, secret="sitting", pid=os.getpid())


def test_parse_mail_to_cli_json_objects_and_strings():
    raw = json.dumps(
        [
            {"deskId": "bob", "roster": "builder"},
            {"deskId": "carol"},
            "dave",
        ]
    )
    got = parse_mail_to_cli_json(raw)
    assert got == [
        {"deskId": "bob", "roster": "builder"},
        {"deskId": "carol"},
        {"deskId": "dave"},
    ]


def test_parse_mail_to_cli_json_bad():
    with pytest.raises(CoordError):
        parse_mail_to_cli_json('{"deskId":"x"}')  # not array
    with pytest.raises(CoordError):
        parse_mail_to_cli_json("{deskId:x}")  # stripped object, not an array
    with pytest.raises(CoordError):
        parse_mail_to_cli_json("[{]")


def test_parse_mail_to_cli_json_powershell_stripped_and_bare():
    """PS5 strips unescaped quotes. Escaped quotes arrive as real JSON."""
    assert parse_mail_to_cli_json('[{"deskId":"grok-tui"}]') == [
        {"deskId": "grok-tui"}
    ]
    assert parse_mail_to_cli_json('[{"deskId":"bob","roster":"builder"}]') == [
        {"deskId": "bob", "roster": "builder"}
    ]
    assert parse_mail_to_cli_json("[{deskId:grok-tui}]") == [{"deskId": "grok-tui"}]
    assert parse_mail_to_cli_json("[grok-tui]") == [{"deskId": "grok-tui"}]
    assert parse_mail_to_cli_json("[grok-tui,carol]") == [
        {"deskId": "grok-tui"},
        {"deskId": "carol"},
    ]
    assert parse_mail_to_cli_json(
        "[{deskId:grok-tui,roster:builder},{deskId:carol}]"
    ) == [
        {"deskId": "grok-tui", "roster": "builder"},
        {"deskId": "carol"},
    ]
    assert parse_mail_to_cli_json("[{deskId:grok-tui,roster:null}]") == [
        {"deskId": "grok-tui", "roster": None}
    ]
    assert parse_mail_to_cli_json("grok-tui") == [{"deskId": "grok-tui"}]
    assert parse_mail_to_cli_json("grok-tui, carol") == [
        {"deskId": "grok-tui"},
        {"deskId": "carol"},
    ]


def _parse_mill(argv):
    """Parse argv through mill main argparse without HTTP."""
    from agent_coord.__main__ import main

    captured = {}

    def fake_http(body):
        captured["body"] = body
        return {
            "id": 1,
            "sender": {"deskId": body.get("src") or body.get("owner"), "roster": None},
            "mail_tos": body.get("mail_tos") or [],
            "body": body.get("body"),
        }

    with patch("agent_coord.client.http.mill_http_call", side_effect=fake_http), patch(
        "agent_coord.client.http.mill_url", return_value="https://wall.test/"
    ), patch(
        "agent_coord.client.tokens.apply_session_token_env"
    ), patch(
        "agent_coord.client.offices.bind_cli_office"
    ), patch(
        "agent_coord.client.offices.pull_office_flag",
        side_effect=lambda raw: (None, list(raw)),
    ):
        try:
            main(list(argv))
        except SystemExit:
            pass
    return captured.get("body")


def test_cli_rejects_owner_flag_on_send(monkeypatch, tmp_path):
    _active(monkeypatch, tmp_path, "alice")
    from agent_coord.__main__ import main
    import io
    from contextlib import redirect_stdout, redirect_stderr

    buf = io.StringIO()
    err = io.StringIO()
    code = 0
    with redirect_stdout(buf), redirect_stderr(err):
        try:
            code = main(["send", "--body-file", "x", "--to-desk", "bob", "--owner", "eve"]) or 0
        except SystemExit as e:
            code = e.code if e.code is not None else 0
    text = buf.getvalue() + err.getvalue()
    assert code not in (0, None) or "unrecognized arguments" in text or "error" in text.lower()
    assert "--owner" in text or code not in (0, None)




# #241: the body comes only from --body-file; --to-desk repeats; no legacy forms.


def _body(tmp_path, text="hello room"):
    f = tmp_path / "body.txt"
    f.write_text(text, encoding="utf-8")
    return str(f)


def test_cli_send_body_file_and_repeat_to_desk(monkeypatch, tmp_path):
    _active(monkeypatch, tmp_path, "alice")
    got = _parse_mill(
        ["send", "--body-file", _body(tmp_path), "--to-desk", "bob", "--to-desk", "carol",
         "--roster", "builder", "--room", "standup"]
    )
    assert "parent_type" not in got and "parent_id" not in got
    assert got["body"] == "hello room"
    assert got["src"] == "alice"
    assert got["mail_tos"] == ["bob", "carol"]
    assert got["roster"] == "builder"
    assert got["name"] == "standup"
    assert "project" not in got  # the seat names the sender project


@pytest.mark.parametrize(
    "argv",
    [
        ["send", "inline body", "--to-desk", "bob"],
        ["send", "the-mill", "alice", "bob", "legacy"],
        ["send", "--body-file", "x", "--mail-to", '["bob"]'],
        ["send", "--body-file", "x", "--to-desk", "bob", "--reason", "builder"],
        ["send", "--body-file", "x", "--to-desk", "bob", "--broadcast"],
        ["send", "--to-desk", "bob"],
        ["reply", "5", "inline body"],
        ["reply", "5", "--body-file", "x", "--mail-to", '["bob"]'],
        ["reply", "5", "--body-file", "x", "--to-add", "bob"],
        ["reply", "5", "--body-file", "x", "--to-drop", "bob"],
        ["reply", "5", "--body-file", "x", "--reason", "builder"],
        ["thread", "the-mill", "--msg", "hi", "--send_to", "bob"],
    ],
)
def test_cli_legacy_send_forms_refused(monkeypatch, tmp_path, argv):
    _active(monkeypatch, tmp_path, "alice")
    assert _parse_mill(argv) is None


def test_cli_reply_shape(monkeypatch, tmp_path):
    _active(monkeypatch, tmp_path, "alice")
    got = _parse_mill(["reply", "7", "--body-file", _body(tmp_path, "ack")])
    assert got["mail_id"] == 7
    assert got["body"] == "ack"
    assert "add_to" not in got and "remove_to" not in got
    assert "project" not in got
    got = _parse_mill(["reply", "7", "--body-file", _body(tmp_path), "--to-desk", "bob"])
    assert got["mail_tos"] == ["bob"]


def test_cli_empty_to_desk_refused(monkeypatch, tmp_path):
    from agent_coord.client.outbound import body_from_args
    from agent_coord.__main__ import _build_parser

    _active(monkeypatch, tmp_path, "alice")
    args = _build_parser().parse_args(["send", "--body-file", _body(tmp_path), "--to-desk", ""])
    with pytest.raises(CoordError, match="--to-desk needs a desk name"):
        body_from_args(args)
