# -*- coding: utf-8 -*-
from agent_coord.helpers.errors import CoordError
from agent_coord.server.admin import human


def test_redeem_collect_requires_token(monkeypatch):
    monkeypatch.setattr("agent_coord.server.admin.door.match_key", lambda t: None)
    try:
        human.redeem_collect("")
        raise AssertionError("expected CoordError")
    except CoordError:
        pass
    try:
        human.redeem_collect("nope")
        raise AssertionError("expected CoordError")
    except CoordError as e:
        assert "not active" in str(e)


def test_redeem_collect_active(monkeypatch):
    monkeypatch.setattr(
        "agent_coord.server.admin.door.match_key",
        lambda t: {"label": "phone", "created_by": "build-ui", "key_id": "ab"},
    )
    row = human.redeem_collect("tok")
    assert row["ok"] is True
    assert row["human"] == "phone"
    assert row["token"] == "tok"


def test_desk_post_requires_invite(monkeypatch):
    monkeypatch.setattr("agent_coord.server.admin.door.check", lambda t: False)
    try:
        human.desk_post(object(), {"token": "x", "body": "hi", "dst": "desk-a"})
        raise AssertionError("expected CoordError")
    except CoordError as e:
        assert "invite" in str(e)


def test_desk_post_send(monkeypatch):
    monkeypatch.setattr("agent_coord.server.admin.door.check", lambda t: True)
    monkeypatch.setattr(
        "agent_coord.server.records.join.desk_for_token_hash",
        lambda cn, digest: "desk-a",
    )
    monkeypatch.setattr(
        "agent_coord.server.records.mail.insert",
        lambda cn, p, src, dst, body, **_k: [{"id": 7}],
    )
    monkeypatch.setattr("agent_coord.server.push.fanout", lambda *a, **k: None)
    row = human.desk_post(
        object(),
        {"token": "t", "src": "desk-a", "dst": "build-ui", "body": "hello", "project": "mill"},
    )
    assert row["ok"] is True
    assert row["id"] == 7


def test_desk_post_rejects_star(monkeypatch):
    monkeypatch.setattr("agent_coord.server.admin.door.check", lambda t: True)
    monkeypatch.setattr(
        "agent_coord.server.records.join.desk_for_token_hash",
        lambda cn, digest: "desk-a",
    )
    try:
        human.desk_post(object(), {"token": "t", "body": "hi", "dst": "*"})
        raise AssertionError("expected CoordError")
    except CoordError:
        pass
