# -*- coding: utf-8 -*-
"""Invite mint is a wall verb. The client does not open the book."""
from __future__ import annotations

from types import SimpleNamespace

from agent_coord.helpers.errors import CoordError
from agent_coord.__main__ import _invite_cmd


def _args(**kw):
    base = dict(
        owner="DESK_admin",
        door="",
        rotate=False,
        mint=False,
        enable="",
        invite_list=False,
        revoke="",
        ttl="",
        ttl_for="",
        label="",
        join="",
        party="human",
        party_id="",
        lan_only=None,
        cmd="invite",
        project="the-mill",
    )
    base.update(kw)
    return SimpleNamespace(**base)


def test_invite_cli_posts_the_verb(monkeypatch, capsys) -> None:
    seen: dict = {}

    def call(body):
        seen.update(body)
        return {
            "ok": True,
            "key_id": "abc123",
            "token": "sekret",
            "invite_path": "/?invite=sekret",
            "status": "pending",
        }

    def no_db(*_a, **_k):
        raise AssertionError("client opened the book")

    monkeypatch.setattr("agent_coord.client.http.mill_http_call", call)
    monkeypatch.setattr("agent_coord.server.records.db.connect", no_db)
    monkeypatch.setattr(
        "agent_coord.client.http.mill_url",
        lambda: "https://203.0.113.10",
    )
    # Session lock: owner from connect session only (argv --owner ignored).
    monkeypatch.setattr(
        "agent_coord.client.tokens.resolve_desk_owner",
        lambda _ignored="": "DESK_admin",
    )
    rc = _invite_cmd(_args(mint=True, label="bot"))
    out = capsys.readouterr().out
    assert rc == 0
    assert seen["verb"] == "invite"
    assert seen["mint"] is True
    assert seen["label"] == "bot"
    assert seen["owner"] == "DESK_admin"
    # #359: the link goes to an owner-only file; stdout names the file.
    assert "sekret" not in out
    assert '"token"' not in out
    assert "mill invite --enable abc123" in out
    assert _link_text(out) == "https://203.0.113.10/?invite=sekret"


def _link_text(out: str) -> str:
    import json
    import os
    from pathlib import Path

    body = out[: out.rindex("}") + 1]
    where = json.loads(body)["link_file"].replace("~", str(Path.home()), 1)
    return Path(os.path.expanduser(where)).read_text(encoding="utf-8").strip()


def test_invite_verb_refuses_non_admin(monkeypatch) -> None:
    from agent_coord.server.api.mill.rpc import _h_invite

    class Book:
        _cn = object()

    def deny(_cn, _desk):
        raise CoordError("mill Admin required (roster Admin member)")

    monkeypatch.setattr("agent_coord.server.admin.guard.require_admin", deny)
    try:
        _h_invite(Book(), {"verb": "invite", "mint": True}, "the-mill", "DESK_alice")
    except CoordError as e:
        assert str(e) == "mill Admin required (roster Admin member)"
        return
    raise AssertionError("non-admin mint was allowed")
