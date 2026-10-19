# -*- coding: utf-8 -*-
"""Verb sender is the parent connect bridge, not the sticky active file."""
from __future__ import annotations

import io
import sys
from types import SimpleNamespace

import pytest

import os

from agent_coord.client import tokens as tokmod
from agent_coord.client import ws as ws_cli
from agent_coord.client.outbound import body_from_args
from agent_coord.client import http as mill_client


def _sit(desk: str) -> None:
    ws_cli.write_rpc_bridge(desk, port=9, secret="sitting", pid=os.getpid())


def test_active_file_is_not_the_verb_sender(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    monkeypatch.delenv("AGENT_COORD_OWNER", raising=False)
    path = tokmod.write_active_desk("builder")
    assert path == tmp_path / "session" / "active"
    assert path.read_text(encoding="utf-8").strip() == "builder"
    assert tokmod.read_active_desk() == "builder"
    assert tokmod.resolve_desk_owner("") == ""
    assert tokmod.resolve_desk_owner("DESK_cli") == ""


def test_resolve_desk_owner_parent_bridge_only(tmp_path, monkeypatch):
    """Actor desk = sitting connect for this parent; CLI/env/active cannot spoof."""
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    monkeypatch.delenv("AGENT_COORD_OWNER", raising=False)
    assert tokmod.resolve_desk_owner("") == ""
    assert tokmod.resolve_desk_owner("DESK_cli") == ""
    tokmod.write_active_desk("DESK_active")
    assert tokmod.resolve_desk_owner("") == ""
    _sit("builder")
    assert tokmod.resolve_desk_owner("") == "builder"
    assert tokmod.resolve_desk_owner("DESK_cli") == "builder"
    monkeypatch.setenv("AGENT_COORD_OWNER", "DESK_env")
    assert tokmod.resolve_desk_owner("") == "builder"
    assert tokmod.resolve_desk_owner("DESK_cli") == "builder"


def test_mill_api_key_uses_sitting_bridge_not_other_token(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    monkeypatch.delenv("AGENT_COORD_OWNER", raising=False)
    monkeypatch.delenv("AGENT_COORD_TOKEN", raising=False)
    tokmod.write_session_token("builder", "tok-builder")
    tokmod.write_session_token("other", "tok-other")
    tokmod.write_active_desk("other")
    assert mill_client.mill_api_key("") == ""
    assert mill_client.mill_api_key("other") == ""
    _sit("builder")
    assert mill_client.mill_api_key("") == "tok-builder"
    assert mill_client.mill_api_key("builder") == "tok-builder"
    assert mill_client.mill_api_key("other") == ""
    empty = tmp_path / "empty"
    empty.mkdir()
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(empty))
    assert mill_client.mill_api_key("") == ""


def test_mill_http_from_args_uses_parent_bridge_not_active_or_argv(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    monkeypatch.delenv("AGENT_COORD_OWNER", raising=False)
    tokmod.write_active_desk("DESK_other")
    _sit("builder")
    captured = {}

    def fake_call(body):
        captured["body"] = body
        return {"ok": True}

    def boom(*_a, **_k):
        raise AssertionError("verb path read active")

    monkeypatch.setattr(mill_client, "mill_http_call", fake_call)
    monkeypatch.setattr(tokmod, "read_active_desk", boom)
    args = SimpleNamespace(
        cmd="todo",
        project="the-mill",
        owner="DESK_spoof",
        need="",
        done=False,
        status="",
        fixtures=False,
    )
    assert mill_client.mill_http_from_args(args) == 0
    assert captured["body"]["owner"] == "builder"


def test_body_uses_parent_bridge_not_active(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    monkeypatch.delenv("AGENT_COORD_OWNER", raising=False)
    tokmod.write_active_desk("DESK_other")
    _sit("builder")

    def boom(*_a, **_k):
        raise AssertionError("verb path read active")

    monkeypatch.setattr(tokmod, "read_active_desk", boom)
    got = body_from_args(
        SimpleNamespace(cmd="todo", project="the-mill", need="", owner="DESK_spoof")
    )
    assert got["owner"] == "builder"


def test_day_one_parsers_have_no_owner_flag(monkeypatch):
    import agent_coord.__main__ as m

    verbs = (
        ["todo", "--help"],
        ["inbox", "--help"],
        ["send", "--help"],
        ["reply", "--help"],
        ["mail-thread", "--help"],
        ["claim", "--help"],
        ["pass", "--help"],
        ["hold", "--help"],
        ["drop", "--help"],
        ["unclaim", "--help"],
        ["unpark", "--help"],
        ["create", "todo", "--help"],
        ["connect", "--help"],
    )
    for argv in verbs:
        buf = io.StringIO()
        old_out, old_err, old_argv = sys.stdout, sys.stderr, sys.argv
        try:
            sys.stdout = buf
            sys.stderr = buf
            sys.argv = ["mill", *argv]
            try:
                m.main()
            except SystemExit as e:
                assert e.code in (0, None)
            text = buf.getvalue()
        finally:
            sys.stdout, sys.stderr, sys.argv = old_out, old_err, old_argv
        assert "--owner" not in text, argv
        assert "AGENT_COORD_OWNER" not in text, argv


def test_connect_help_has_desk_positional():
    import agent_coord.__main__ as m

    buf = io.StringIO()
    old_out, old_err, old_argv = sys.stdout, sys.stderr, sys.argv
    try:
        sys.stdout = buf
        sys.stderr = buf
        sys.argv = ["mill", "connect", "--help"]
        try:
            m.main()
        except SystemExit as e:
            assert e.code in (0, None)
        text = buf.getvalue()
    finally:
        sys.stdout, sys.stderr, sys.argv = old_out, old_err, old_argv
    assert "desk" in text.lower()
    assert "--owner" not in text
