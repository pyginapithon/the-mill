# -*- coding: utf-8 -*-
"""The human Wall ACL and the glance keypad lockout read X-Forwarded-For only
from a trusted proxy, like door=ip (#731, after #651).

A private or loopback peer that is not a trusted proxy is judged by its own
address. From a trusted proxy the client is the rightmost hop that is not a
proxy, and a forwarded loopback address is not this machine.
"""
from __future__ import annotations

from pathlib import Path

import pytest

# 192.0.2.0/24 (documentation) counts as private in ipaddress, like a LAN peer.
PRIVATE_PEER = "192.0.2.40"
ALLOWED = "203.0.113.1"
TAPS = ["aaaaaaaaaa", "bbbbbbbbbb", "cccccccccc", "dddddddddd"]


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.delenv("AGENT_COORD_TRUSTED_PROXIES", raising=False)
    monkeypatch.setattr("agent_coord.server.admin.door.mode", lambda: "path")


def _client(monkeypatch, peer: str, *, allow: str = ALLOWED, api_only: bool = False):
    from fastapi.testclient import TestClient

    from agent_coord.lib.observe import parse_roots
    from agent_coord.server.asgi import make_asgi_app

    if allow:
        monkeypatch.setenv("AGENT_COORD_WALL_ALLOW", allow)
    else:
        monkeypatch.delenv("AGENT_COORD_WALL_ALLOW", raising=False)
    here = Path(__file__).resolve().parents[2]
    app = make_asgi_app(parse_roots(cwd=here), api_only=api_only)
    return TestClient(app, client=(peer, 50000))


def _acl(r) -> bool:
    return r.status_code == 403 and b"human Wall ACL" in r.content


# --- human Wall ACL -------------------------------------------------------


def test_private_peer_forged_allowed_address_is_refused(monkeypatch) -> None:
    c = _client(monkeypatch, PRIVATE_PEER)
    assert _acl(c.get("/", headers={"X-Forwarded-For": ALLOWED}))
    assert _acl(c.get("/", headers={"X-Forwarded-For": "127.0.0.1"}))


def test_loopback_proxy_forwarded_loopback_is_not_this_machine(monkeypatch) -> None:
    c = _client(monkeypatch, "127.0.0.1")
    assert _acl(c.get("/", headers={"X-Forwarded-For": "127.0.0.1"}))


def test_loopback_proxy_reads_the_hop_it_appended(monkeypatch) -> None:
    c = _client(monkeypatch, "127.0.0.1")
    # nginx appends the real peer on the right; a spoofed left entry is unused.
    assert _acl(c.get("/", headers={"X-Forwarded-For": f"{ALLOWED}, 198.51.100.7"}))
    assert not _acl(c.get("/", headers={"X-Forwarded-For": f"198.51.100.7, {ALLOWED}"}))


def test_direct_clients_unchanged(monkeypatch) -> None:
    assert not _acl(_client(monkeypatch, ALLOWED).get("/"))
    assert _acl(_client(monkeypatch, PRIVATE_PEER).get("/"))
    assert not _acl(_client(monkeypatch, "127.0.0.1").get("/"))
    # Empty list: the human Wall stays open, forwarded or not.
    c = _client(monkeypatch, PRIVATE_PEER, allow="")
    assert not _acl(c.get("/", headers={"X-Forwarded-For": "198.51.100.7"}))


# --- glance keypad lockout ------------------------------------------------


@pytest.fixture
def armed(monkeypatch):
    from agent_coord.server.glance import _misses, _sessions, digest_for

    _sessions.clear()
    _misses.clear()
    monkeypatch.setenv("AGENT_COORD_GLANCE_TAP", digest_for(TAPS, "word"))
    yield
    _sessions.clear()
    _misses.clear()


def _tap(c, xff: str, *, good: bool):
    taps = TAPS if good else ["zzzzzzzzzz"] * 4
    return c.post(
        "/api/v1/glance/tap",
        json={"taps": taps, "passphrase": "word"},
        headers={"X-Forwarded-For": xff} if xff else {},
    )


def test_rotating_forged_address_still_locks_out(monkeypatch, armed) -> None:
    c = _client(monkeypatch, PRIVATE_PEER, allow="", api_only=True)
    for n in range(6):
        assert _tap(c, f"198.51.100.{n + 1}", good=False).status_code == 404
    # The sixth wrong guess came from the same peer, so the right one is held.
    assert _tap(c, "198.51.100.99", good=True).status_code == 404


def test_rotating_spoofed_left_hop_through_proxy_still_locks_out(monkeypatch, armed) -> None:
    c = _client(monkeypatch, "127.0.0.1", allow="", api_only=True)
    for n in range(6):
        xff = f"198.51.100.{n + 1}, 203.0.113.50"
        assert _tap(c, xff, good=False).status_code == 404
    assert _tap(c, "198.51.100.99, 203.0.113.50", good=True).status_code == 404
    # Another real client behind the same proxy is not locked out.
    assert _tap(c, "203.0.113.51", good=True).status_code == 200


def test_direct_client_keypad_unchanged(monkeypatch, armed) -> None:
    c = _client(monkeypatch, PRIVATE_PEER, allow="", api_only=True)
    assert _tap(c, "", good=False).status_code == 404
    assert _tap(c, "", good=True).status_code == 200
