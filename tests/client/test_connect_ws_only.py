# -*- coding: utf-8 -*-
"""mill connect sits on /ws. It does not POST the join command.
mill join = tokenhash+cert; mill connect = establish desk id.
"""
from types import SimpleNamespace

from agent_coord.server.records import join as rec_join
from agent_coord.client.http import mill_here_over_http


def _args(**kw):
    base = dict(
        cmd="connect",
        desk="builder",
        project="the-mill",
        doing="present",
        role="",
        root="",
        reset=False,
        vendor="",
        session="",
        foreground=True,
    )
    base.update(kw)
    return SimpleNamespace(**base)


def test_connect_does_not_post_join(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    posted = []
    monkeypatch.setattr(
        "agent_coord.client.http.mill_http_call",
        lambda body: posted.append(body),
    )
    monkeypatch.setattr(
        "agent_coord.client.http.resolve_desk_owner",
        lambda cli="": "builder",
    )
    monkeypatch.setattr(
        "agent_coord.client.tokens.read_session_token",
        lambda owner, **k: "session-token",
    )
    monkeypatch.setattr(
        "agent_coord.client.ws.wait_one_hint",
        lambda desk, token, **k: {"ok": True, "hint": "MAIL", "id": 1},
    )
    code = mill_here_over_http(_args())
    assert code == 0
    assert posted == []


def test_connect_without_token_does_not_sit(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    monkeypatch.setattr(
        "agent_coord.client.http.resolve_desk_owner",
        lambda cli="": "builder",
    )
    monkeypatch.setattr(
        "agent_coord.client.tokens.read_session_token",
        lambda owner, **k: "",
    )
    monkeypatch.setattr(
        "agent_coord.client.ws.start_ws_thread",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("no socket")),
    )
    assert mill_here_over_http(_args(foreground=False)) == 1


def test_note_connect_calls_activity_procedure(monkeypatch) -> None:
    seen = []
    monkeypatch.setattr(
        "agent_coord.server.records.join.call",
        lambda cn, name, args: seen.append((name, args)) or [],
    )
    rec_join.note_connect(object(), "builder")
    assert seen == [("mill_join_connect", ["builder"])]
