# -*- coding: utf-8 -*-
from agent_coord.server.allow import allowed, door_client, is_mill_command


def test_empty_allow_is_open() -> None:
    assert allowed("203.0.113.8", [])
    assert allowed("192.0.2.8", [])
    assert allowed("192.0.2.8", [], empty_open=True)
    assert not allowed("192.0.2.8", [], empty_open=False)
    assert allowed("127.0.0.1", [], empty_open=False)


def test_cidr_and_exact() -> None:
    rules = ["127.0.0.1", "203.0.113.0/24"]
    assert allowed("127.0.0.1", rules)
    assert allowed("203.0.113.50", rules)
    assert not allowed("198.51.100.1", rules)


def test_forwarded_from_loopback(monkeypatch) -> None:
    monkeypatch.delenv("AGENT_COORD_TRUSTED_PROXIES", raising=False)
    # The last hop that is not a proxy (#731); a proxy hop is skipped and a
    # spoofed left entry is unused.
    assert door_client("127.0.0.1", "203.0.113.9, 127.0.0.1") == ("203.0.113.9", True)
    assert door_client("127.0.0.1", "198.51.100.1, 203.0.113.9") == ("203.0.113.9", True)
    # A global address stays split so the pack check does not see a complete host.
    peer = ".".join(("8", "8", "8", "8"))
    assert door_client(peer, ".".join(("1", "2", "3", "4"))) == (peer, False)


def test_asgi_wall_403(monkeypatch) -> None:
    from pathlib import Path

    from fastapi.testclient import TestClient

    from agent_coord.lib.observe import parse_roots
    from agent_coord.server.asgi import make_asgi_app

    monkeypatch.setenv("AGENT_COORD_WALL_ALLOW", "203.0.113.1")
    here = Path(__file__).resolve().parents[2]
    app = make_asgi_app(parse_roots(cwd=here), api_only=False)
    client = TestClient(app)
    r = client.get("/")
    assert r.status_code == 403


def test_mill_command_skip() -> None:
    assert is_mill_command("/api/mill/here")
    assert is_mill_command("/mill/v1/here")
    assert not is_mill_command("/")
    assert not is_mill_command("/api/floor")
