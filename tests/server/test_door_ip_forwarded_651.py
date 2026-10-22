# -*- coding: utf-8 -*-
"""door=ip trusts X-Forwarded-For only from a configured proxy (#651)."""
from __future__ import annotations

from pathlib import Path

import pytest

from agent_coord.server.allow import allowed, client_ip, door_client

# 192.0.2.0/24 (documentation) counts as private in ipaddress, like a LAN peer.
PRIVATE_PEER = "192.0.2.40"
RULES = ["203.0.113.1"]


@pytest.fixture(autouse=True)
def _no_proxy_env(monkeypatch):
    monkeypatch.delenv("AGENT_COORD_TRUSTED_PROXIES", raising=False)


def test_private_peer_forwarded_loopback_is_denied() -> None:
    ip, via = door_client(PRIVATE_PEER, "127.0.0.1")
    assert (ip, via) == (PRIVATE_PEER, False)
    assert not allowed(ip, RULES, empty_open=False, forwarded=via)


def test_private_peer_forwarded_allowed_client_is_ignored() -> None:
    ip, via = door_client(PRIVATE_PEER, "203.0.113.1")
    assert (ip, via) == (PRIVATE_PEER, False)
    assert not allowed(ip, RULES, empty_open=False, forwarded=via)


def test_forwarded_loopback_is_not_the_local_machine() -> None:
    ip, via = door_client("127.0.0.1", "127.0.0.1")
    assert (ip, via) == ("127.0.0.1", True)
    assert not allowed(ip, RULES, empty_open=False, forwarded=via)
    assert not allowed(ip, [], empty_open=False, forwarded=via)
    assert allowed(ip, ["127.0.0.1"], empty_open=False, forwarded=via)


def test_direct_loopback_stays_the_local_machine() -> None:
    assert door_client("127.0.0.1", "") == ("127.0.0.1", False)
    assert door_client("::1", "") == ("::1", False)
    assert allowed("127.0.0.1", RULES, empty_open=False)
    assert allowed("::1", [], empty_open=False)


def test_loopback_proxy_reads_the_hop_it_appended() -> None:
    # nginx appends the real peer; a spoofed left entry is never used.
    assert door_client("127.0.0.1", "127.0.0.1, 203.0.113.1") == ("203.0.113.1", True)
    assert door_client("127.0.0.1", "203.0.113.1, 198.51.100.7") == ("198.51.100.7", True)
    ip, via = door_client("127.0.0.1", "203.0.113.1, 198.51.100.7")
    assert not allowed(ip, RULES, empty_open=False, forwarded=via)
    ip, via = door_client("127.0.0.1", "198.51.100.7, 203.0.113.1")
    assert allowed(ip, RULES, empty_open=False, forwarded=via)


def test_configured_proxy(monkeypatch) -> None:
    monkeypatch.setenv("AGENT_COORD_TRUSTED_PROXIES", "192.0.2.0/25")
    assert door_client(PRIVATE_PEER, "203.0.113.1") == ("203.0.113.1", True)
    assert door_client("192.0.2.200", "203.0.113.1") == ("192.0.2.200", False)
    # A configured list replaces the loopback default.
    assert door_client("127.0.0.1", "203.0.113.1") == ("127.0.0.1", False)


def test_bad_forwarded_entry_is_denied() -> None:
    ip, via = door_client("127.0.0.1", "not-an-ip")
    assert via
    assert not allowed(ip, RULES, empty_open=False, forwarded=via)


def test_client_ip_unchanged_for_path_and_directory() -> None:
    assert client_ip("127.0.0.1", "203.0.113.9, 127.0.0.1") == "203.0.113.9"
    assert client_ip(PRIVATE_PEER, "203.0.113.9") == "203.0.113.9"


def _app(monkeypatch, door: str):
    from agent_coord.lib.observe import parse_roots
    from agent_coord.server.asgi import make_asgi_app

    monkeypatch.setenv("AGENT_COORD_DOOR", door)
    monkeypatch.setenv("AGENT_COORD_WALL_ALLOW", RULES[0])
    here = Path(__file__).resolve().parents[2]
    return make_asgi_app(parse_roots(cwd=here), api_only=False)


def test_asgi_door_ip_private_peer_forwarded_loopback_403(monkeypatch) -> None:
    from fastapi.testclient import TestClient

    app = _app(monkeypatch, "ip")
    c = TestClient(app, client=(PRIVATE_PEER, 50000))
    r = c.get("/api/floor", headers={"X-Forwarded-For": "127.0.0.1"})
    assert r.status_code == 403
    assert b"door=ip" in r.content
    r = c.get("/api/floor", headers={"X-Forwarded-For": RULES[0]})
    assert r.status_code == 403


def test_asgi_door_ip_direct_loopback_passes(monkeypatch) -> None:
    from fastapi.testclient import TestClient

    app = _app(monkeypatch, "ip")
    r = TestClient(app, client=("127.0.0.1", 50000)).get("/api/floor")
    assert r.status_code != 403
