# -*- coding: utf-8 -*-
"""Security: join (new-desk mint) is gated by the office door (#sec S-2).

Behavior under test: a cold desk cannot mint a session at a gated office
(invite / directory / iam) without a valid invite or seat. A path office stays
open, a valid seat joins, a reconnecting desk's own token joins, and the
loopback office host (installer) always joins.
"""
from __future__ import annotations

import pytest

from agent_coord.helpers.errors import CoordError
from agent_coord.server.api.mill import rpc
from agent_coord.server.api.mill.rpc import dispatch


class _FakeBook:
    _tokens: dict = {}
    _cn = object()

    def resolve_bearer(self, token):  # join never calls this (open command)
        return ""

    def _guard_owner(self, *a, **k):
        return {}


@pytest.fixture
def seen(monkeypatch):
    """Record whether the join handler ran; stub it so no DB is touched."""
    calls = {}

    def _stub(c, body, project, owner):
        calls["ran"] = True
        calls["owner"] = owner
        return {"ok": True, "owner": owner, "token": "minted"}

    monkeypatch.setattr("agent_coord.server.api.mill.rpc._h_here", _stub)
    # Keep the HANDLERS table pointing at the stub too.
    monkeypatch.setitem(rpc.HANDLERS, "join", _stub)
    return calls


def _door(monkeypatch, *, check: bool, seat: bool):
    monkeypatch.setattr("agent_coord.server.admin.door.check", lambda t: check)
    monkeypatch.setattr("agent_coord.server.admin.seats.seat_known", lambda t: seat)


def test_cold_desk_cannot_mint_session_at_gated_office(monkeypatch, seen):
    # Gated door (invite/directory/iam): check() false, no seat, no credential.
    _door(monkeypatch, check=False, seat=False)
    with pytest.raises(CoordError) as exc:
        dispatch(
            _FakeBook(),
            {"verb": "join", "project": "the-mill", "owner": "zz-intruder"},
            token="",
        )
    assert "join refused" in str(exc.value).lower()
    assert "ran" not in seen  # handler never reached: nothing minted


def test_path_office_join_stays_open(monkeypatch, seen):
    # path/ip office: door.check returns True with no credential.
    _door(monkeypatch, check=True, seat=False)
    out = dispatch(
        _FakeBook(),
        {"verb": "join", "project": "the-mill", "owner": "newdesk"},
        token="",
    )
    assert out["ok"] is True
    assert seen.get("ran") is True


def test_valid_seat_joins_gated_office(monkeypatch, seen):
    # Gated door, but the presented token is a known seat.
    _door(monkeypatch, check=False, seat=True)
    out = dispatch(
        _FakeBook(),
        {"verb": "join", "project": "the-mill", "owner": "seated", "token": "seat-xyz"},
        token="seat-xyz",
    )
    assert out["ok"] is True
    assert seen.get("ran") is True


def test_reconnect_with_own_token_joins(monkeypatch, seen):
    # A reconnecting desk presents its own session token, whose hash is a
    # join.token_hash, so seat_known recognizes it.
    _door(monkeypatch, check=False, seat=True)
    out = dispatch(
        _FakeBook(),
        {"verb": "join", "project": "the-mill", "owner": "backagain", "token": "own-sess"},
        token="own-sess",
    )
    assert out["ok"] is True
    assert seen.get("ran") is True


def test_loopback_office_host_always_joins(monkeypatch, seen):
    # Installer on the box: mark_host set host=True from the loopback peer.
    _door(monkeypatch, check=False, seat=False)
    out = dispatch(
        _FakeBook(),
        {"verb": "join", "project": "the-mill", "owner": "installer", "host": True},
        token="",
    )
    assert out["ok"] is True
    assert seen.get("ran") is True


def test_empty_credential_at_gated_office_refused_not_seat_checked(monkeypatch, seen):
    # Edge: no credential at a gated door must refuse even though seat_known
    # would be consulted only for a non-empty candidate.
    called = {"seat": 0}

    def _seat(t):
        called["seat"] += 1
        return False

    monkeypatch.setattr("agent_coord.server.admin.door.check", lambda t: False)
    monkeypatch.setattr("agent_coord.server.admin.seats.seat_known", _seat)
    with pytest.raises(CoordError):
        dispatch(
            _FakeBook(),
            {"verb": "join", "project": "the-mill", "owner": "nobody"},
            token="",
        )
    assert called["seat"] == 0  # empty candidate never hits the seat lookup
