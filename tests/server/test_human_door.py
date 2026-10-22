"""Human wall bearer. Agent calls do not present a directory token."""

from __future__ import annotations

from agent_coord.client.tokens import token_hash
from agent_coord.server.admin.human import agent_call, allows, seat


def test_mill_command_is_the_agent_door():
    assert agent_call("/mill/v1/join") is True
    assert agent_call("/") is False
    assert agent_call("/board") is False


def test_allows_checks_the_stored_hash(monkeypatch):
    opened: dict[str, str] = {}

    def _open(cn, digest):
        opened["digest"] = digest
        return [{"id": 3}]

    monkeypatch.setattr("agent_coord.server.records.human.open", _open)
    monkeypatch.setattr("agent_coord.server.admin.human._office", lambda: object())
    assert allows("human-bearer") is True
    assert opened["digest"] == token_hash("human-bearer")
    assert allows("") is False


def test_allows_fails_closed_when_the_office_is_down(monkeypatch):
    monkeypatch.setattr("agent_coord.server.admin.human._office", lambda: None)
    assert allows("human-bearer") is False


def test_seat_stores_the_hash_and_returns_a_new_bearer(monkeypatch):
    monkeypatch.setattr(
        "agent_coord.server.admin.human._identity",
        lambda token: {"sub": "person-1", "kind": "human", "roles": ["Admin"]},
    )
    stored: dict[str, str] = {}

    def _put(cn, digest, subject, role):
        stored["digest"] = digest
        stored["subject"] = subject
        stored["role"] = role
        return [{"id": 1}]

    monkeypatch.setattr("agent_coord.server.records.human.put", _put)
    monkeypatch.setattr("agent_coord.server.admin.human._office", lambda: object())
    bearer = seat("header.payload.sig")
    assert bearer
    assert bearer != "header.payload.sig"
    assert stored == {
        "digest": token_hash(bearer),
        "subject": "person-1",
        "role": "Admin",
    }


def test_seat_refuses_an_agent_token(monkeypatch):
    monkeypatch.setattr(
        "agent_coord.server.admin.human._identity",
        lambda token: {"sub": "bot-1", "kind": "agent", "roles": []},
    )
    assert seat("header.payload.sig") == ""
