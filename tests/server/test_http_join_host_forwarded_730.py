# -*- coding: utf-8 -*-
"""HTTP join marks the office host only for a direct loopback peer (#730).

Behind the installed nginx edge every request reaches the wall from loopback
with X-Forwarded-For set. Such a request is not the office host, so a gated
door (invite / directory / iam) refuses an unauthenticated join. A direct
loopback join with no forwarded header is still the host. WS already did this.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from agent_coord.server.admin.guard import mark_host
from agent_coord.server.api.mill import rpc


class _FakeBook:
    _tokens: dict = {}
    _cn = object()
    acting_desk = ""

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def resolve_bearer(self, token):
        return ""

    def _guard_owner(self, *a, **k):
        return {}


@pytest.fixture
def seen(monkeypatch):
    calls: dict = {}

    def _stub(c, body, project, owner):
        calls["ran"] = True
        calls["host"] = body.get("host")
        return {"ok": True, "owner": owner, "token": "minted"}

    monkeypatch.setattr("agent_coord.server.api.mill.rpc._h_here", _stub)
    monkeypatch.setitem(rpc.HANDLERS, "join", _stub)
    monkeypatch.setattr("agent_coord.server.admin.door.mode", lambda: "directory")
    monkeypatch.setattr("agent_coord.server.admin.door.check", lambda t: False)
    monkeypatch.setattr("agent_coord.server.admin.seats.seat_known", lambda t: False)
    monkeypatch.setattr("agent_coord.server.middleware._office", lambda: _FakeBook())
    monkeypatch.setattr(
        "agent_coord.server.records.join.set_lan_ip", lambda *a, **k: None
    )
    return calls


def _client(peer: str):
    from fastapi.testclient import TestClient

    from agent_coord.lib.observe import parse_roots
    from agent_coord.server.asgi import make_asgi_app

    here = Path(__file__).resolve().parents[2]
    app = make_asgi_app(parse_roots(cwd=here), api_only=False)
    return TestClient(app, client=(peer, 50000))


def _join(c, headers=None):
    return c.post(
        "/mill/v1/join",
        json={"project": "the-mill", "owner": "zz-outsider"},
        headers=headers or {},
    )


def test_forwarded_join_through_loopback_proxy_is_refused(seen) -> None:
    r = _join(_client("127.0.0.1"), {"X-Forwarded-For": "203.0.113.9"})
    assert r.status_code != 200
    assert b"minted" not in r.content
    assert "ran" not in seen


def test_forwarded_loopback_value_is_not_the_host(seen) -> None:
    r = _join(_client("127.0.0.1"), {"X-Forwarded-For": "127.0.0.1"})
    assert r.status_code != 200
    assert "ran" not in seen


def test_direct_loopback_join_is_still_the_host(seen) -> None:
    r = _join(_client("127.0.0.1"))
    assert r.status_code == 200
    assert seen.get("ran") is True
    assert seen.get("host") is True


def test_remote_peer_is_never_the_host(seen) -> None:
    r = _join(_client("203.0.113.9"))
    assert r.status_code != 200
    assert "ran" not in seen


def test_mark_host_forwarded_never_marks() -> None:
    d = {"host": True}
    mark_host(d, "127.0.0.1", forwarded=True)
    assert "host" not in d
    d = {}
    mark_host(d, "127.0.0.1")
    assert d.get("host") is True
    d = {"host": True}
    mark_host(d, "203.0.113.9")
    assert "host" not in d
