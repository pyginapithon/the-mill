"""#391/#397 session token: per-desk file only, never env."""
from __future__ import annotations

import os

import pytest

from agent_coord.client import tokens as tokmod
from agent_coord.client import http as mill_client


def test_write_refuses_cross_desk_alias(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    tokmod.write_session_token("alpha", "secret-token-aaa")
    with pytest.raises(ValueError, match="already bound"):
        tokmod.write_session_token("beta", "secret-token-aaa")


def test_write_same_desk_again(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    tokmod.write_session_token("alpha", "secret-token-bbb")
    tokmod.write_session_token("alpha", "secret-token-bbb")
    assert tokmod.read_session_token("alpha") == "secret-token-bbb"


def test_mill_api_key_ignores_env_token(tmp_path, monkeypatch):
    from agent_coord.client.ws import write_rpc_bridge

    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    tokmod.write_session_token("me", "file-token")
    write_rpc_bridge("me", port=9, secret="sitting", pid=os.getpid())
    monkeypatch.setenv("AGENT_COORD_TOKEN", "env-must-not-win")
    assert mill_client.mill_api_key("me") == "file-token"
    assert mill_client.mill_api_key("ghost") == ""
    empty = tmp_path / "empty"
    empty.mkdir()
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(empty))
    monkeypatch.setenv("AGENT_COORD_TOKEN", "env-only")
    assert mill_client.mill_api_key("ghost") == ""


def test_apply_session_token_env_is_noop(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    tokmod.write_session_token("me", "file-token")
    monkeypatch.delenv("AGENT_COORD_TOKEN", raising=False)
    assert tokmod.apply_session_token_env("me") is False
    assert not os.environ.get("AGENT_COORD_TOKEN")
