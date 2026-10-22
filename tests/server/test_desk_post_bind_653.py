# -*- coding: utf-8 -*-
"""POST /api/desk binds sender and mark-read to the seated desk (#653)."""
from agent_coord.helpers.errors import CoordError
from agent_coord.server.admin import human


def _path(monkeypatch):
    monkeypatch.setattr(human.door, "mode", lambda: "path")


def _seat(monkeypatch, desk):
    monkeypatch.setattr(
        "agent_coord.server.records.join.desk_for_token_hash",
        lambda cn, digest: desk,
    )


def _no_mail(monkeypatch):
    inserted = []
    monkeypatch.setattr(
        "agent_coord.server.records.mail.insert",
        lambda *a, **k: inserted.append((a, k)) or [{"id": 1}],
    )
    monkeypatch.setattr("agent_coord.server.mail_push.push_mail", lambda *a, **k: None)
    return inserted


def _no_opened(monkeypatch):
    opened = []
    monkeypatch.setattr(
        "agent_coord.server.records.opened.insert",
        lambda cn, mid, desk: opened.append((mid, desk)) or None,
    )
    return opened


def test_path_door_forged_sender_writes_nothing(monkeypatch):
    _path(monkeypatch)
    _seat(monkeypatch, "")
    inserted = _no_mail(monkeypatch)
    try:
        human.desk_post(
            object(),
            {
                "token": "anything",
                "src": "other-desk",
                "dst": "build-ui",
                "body": "hello",
                "project": "mill",
            },
        )
        raise AssertionError("expected CoordError")
    except CoordError as e:
        assert "desk session" in str(e)
    assert inserted == []


def test_path_door_other_reader_writes_nothing(monkeypatch):
    _path(monkeypatch)
    _seat(monkeypatch, "desk-a")
    opened = _no_opened(monkeypatch)
    try:
        human.desk_post(
            object(),
            {"token": "seat", "mark_read": True, "desk": "other-desk", "ids": [4]},
        )
        raise AssertionError("expected CoordError")
    except CoordError as e:
        assert "reader" in str(e)
    assert opened == []


def test_path_door_dst_as_reader_writes_nothing(monkeypatch):
    _path(monkeypatch)
    _seat(monkeypatch, "desk-a")
    opened = _no_opened(monkeypatch)
    try:
        human.desk_post(
            object(),
            {"token": "seat", "action": "mark_read", "dst": "other-desk", "ids": [4]},
        )
        raise AssertionError("expected CoordError")
    except CoordError as e:
        assert "reader" in str(e)
    assert opened == []


def test_seated_desk_sends_as_itself(monkeypatch):
    _path(monkeypatch)
    _seat(monkeypatch, "desk-a")
    seen = {}

    def insert(cn, project, src, dst, body, **k):
        seen["src"] = src
        seen["dst"] = dst
        seen["body"] = body
        return [{"id": 7}]

    monkeypatch.setattr("agent_coord.server.records.mail.insert", insert)
    monkeypatch.setattr("agent_coord.server.mail_push.push_mail", lambda *a, **k: None)
    row = human.desk_post(
        object(),
        {"token": "seat", "dst": "build-ui", "body": "hello", "project": "mill"},
    )
    assert row["ok"] is True
    assert row["src"] == "desk-a"
    assert seen["src"] == "desk-a"
    assert seen["dst"] == "build-ui"


def test_seated_desk_may_name_itself(monkeypatch):
    _path(monkeypatch)
    _seat(monkeypatch, "desk-a")
    seen = {}
    monkeypatch.setattr(
        "agent_coord.server.records.mail.insert",
        lambda cn, project, src, dst, body, **k: seen.update(src=src) or [{"id": 8}],
    )
    monkeypatch.setattr("agent_coord.server.mail_push.push_mail", lambda *a, **k: None)
    row = human.desk_post(
        object(),
        {
            "token": "seat",
            "src": "desk-a",
            "dst": "build-ui",
            "body": "hello",
            "project": "mill",
        },
    )
    assert row["src"] == "desk-a"
    assert seen["src"] == "desk-a"


def test_seated_mark_read_uses_that_desk(monkeypatch):
    _path(monkeypatch)
    _seat(monkeypatch, "desk-a")
    opened = _no_opened(monkeypatch)
    row = human.desk_post(
        object(),
        {"token": "seat", "mark_read": True, "ids": [4, 5]},
    )
    assert row == {"ok": True, "n": 2}
    assert opened == [(4, "desk-a"), (5, "desk-a")]


def test_session_secret_seats_when_body_does_not(monkeypatch):
    _path(monkeypatch)

    def lookup(cn, digest):
        from agent_coord.client.tokens import token_hash

        if digest == token_hash("cookie-seat"):
            return "desk-a"
        return ""

    monkeypatch.setattr("agent_coord.server.records.join.desk_for_token_hash", lookup)
    seen = {}
    monkeypatch.setattr(
        "agent_coord.server.records.mail.insert",
        lambda cn, project, src, dst, body, **k: seen.update(src=src) or [{"id": 9}],
    )
    monkeypatch.setattr("agent_coord.server.mail_push.push_mail", lambda *a, **k: None)
    row = human.desk_post(
        object(),
        {"token": "not-a-seat", "src": "desk-a", "dst": "build-ui", "body": "hello"},
        session="cookie-seat",
    )
    assert row["src"] == "desk-a"
    assert seen["src"] == "desk-a"
