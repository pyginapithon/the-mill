"""Invite-key join must not echo the Office placeholder as the seat project (#249)."""
from __future__ import annotations


def _book():
    return type("B", (), {"_cn": object()})()


def _patch(monkeypatch, seated):
    from agent_coord.server.api.mill import rpc

    seen = {}

    def fake_upsert(cn, project, desk, role="", token_hash=None, doing=None):
        seen["project"] = project
        return [{"owner": desk, "desk_id": 3, "id": 9}]

    monkeypatch.setattr("agent_coord.server.records.join.upsert", fake_upsert)
    monkeypatch.setattr("agent_coord.server.records.member.put_office", lambda *a, **k: None)
    monkeypatch.setattr(rpc, "_seat_roster", lambda cn, desk: seated)
    monkeypatch.setattr(rpc, "_poke", lambda *a, **k: None)
    return rpc, seen


def test_connect_office_stays_office(monkeypatch) -> None:
    """0.7.x: mill connect with no roster sends Office on purpose; it is not swapped."""
    rpc, seen = _patch(monkeypatch, "the-mill")
    out = rpc._issue_here(_book(), {"project": "Office", "owner": "build-app"})
    assert seen["project"] == "Office"
    assert out["group_id"] == "Office"


def test_office_placeholder_returns_the_seat_roster(monkeypatch) -> None:
    rpc, seen = _patch(monkeypatch, "the-mill")
    out = rpc._issue_here(_book(), {"project": "Office", "placeholder": True, "owner": "build-app"})
    assert seen["project"] == "the-mill"
    assert out["group_id"] == "the-mill"
    assert out["token"]


def test_unknown_seat_still_echoes_office(monkeypatch) -> None:
    rpc, seen = _patch(monkeypatch, "Office")
    out = rpc._issue_here(_book(), {"project": "Office", "owner": "build-app"})
    assert seen["project"] == "Office"
    assert out["group_id"] == "Office"


def test_explicit_project_is_not_replaced(monkeypatch) -> None:
    rpc, seen = _patch(monkeypatch, "other")
    out = rpc._issue_here(_book(), {"project": "the-mill", "owner": "build-app"})
    assert seen["project"] == "the-mill"
    assert out["group_id"] == "the-mill"
