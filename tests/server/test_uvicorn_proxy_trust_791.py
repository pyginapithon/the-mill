# -*- coding: utf-8 -*-
"""mill-wall hard-sets uvicorn proxy trust; FORWARDED_ALLOW_IPS cannot widen it (#791)."""
from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

PEER = "192.0.2.40"  # not a trusted proxy (default trust is loopback)
ALLOWED = "203.0.113.1"


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.delenv("AGENT_COORD_TRUSTED_PROXIES", raising=False)
    monkeypatch.setenv("AGENT_COORD_DOOR", "ip")
    monkeypatch.setenv("AGENT_COORD_WALL_ALLOW", ALLOWED)


def _config(monkeypatch, fai: str | None):
    from agent_coord.lib.observe import parse_roots
    from agent_coord.server.asgi import make_asgi_app, uvicorn_config

    if fai is None:
        monkeypatch.delenv("FORWARDED_ALLOW_IPS", raising=False)
    else:
        monkeypatch.setenv("FORWARDED_ALLOW_IPS", fai)
    here = Path(__file__).resolve().parents[2]
    app = make_asgi_app(parse_roots(cwd=here), api_only=False)
    cfg = uvicorn_config(app, "127.0.0.1", 0)
    cfg.load()
    return cfg


def _get(cfg, peer: str, fwd: str) -> int:
    """One GET /api/floor through the app exactly as uvicorn loaded it."""
    headers = [(b"host", b"wall.example")]
    if fwd:
        headers.append((b"x-forwarded-for", fwd.encode()))
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "https",
        "path": "/api/floor",
        "raw_path": b"/api/floor",
        "query_string": b"",
        "root_path": "",
        "headers": headers,
        "client": (peer, 50000),
        "server": ("127.0.0.1", 443),
    }
    status: list[int] = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(msg):
        if msg["type"] == "http.response.start":
            status.append(msg["status"])

    asyncio.run(cfg.loaded_app(scope, receive, send))
    return status[0]


@pytest.mark.parametrize("fai", ["*", PEER, "192.0.2.0/24", None])
def test_forged_forwarded_for_from_untrusted_peer_is_403(monkeypatch, fai) -> None:
    cfg = _config(monkeypatch, fai)
    assert _get(cfg, PEER, ALLOWED) == 403
    assert _get(cfg, PEER, "127.0.0.1") == 403
    assert _get(cfg, PEER, "") == 403
    # uvicorn never rewrites the peer; allow.door_client alone reads the header.
    assert cfg.proxy_headers is False


def test_loopback_edge_still_forwards_the_real_client(monkeypatch) -> None:
    # The installed nginx edge (loopback) still names the client, via
    # AGENT_COORD_TRUSTED_PROXIES' loopback default, not uvicorn.
    cfg = _config(monkeypatch, "*")
    assert _get(cfg, "127.0.0.1", f"198.51.100.7, {ALLOWED}") != 403
    assert _get(cfg, "127.0.0.1", f"{ALLOWED}, 198.51.100.7") == 403


def test_trusted_proxies_is_the_only_way_to_widen(monkeypatch) -> None:
    monkeypatch.setenv("AGENT_COORD_TRUSTED_PROXIES", "192.0.2.0/25")
    cfg = _config(monkeypatch, None)
    assert _get(cfg, PEER, ALLOWED) != 403
    assert _get(cfg, "192.0.2.200", ALLOWED) == 403


def test_direct_loopback_still_passes(monkeypatch) -> None:
    cfg = _config(monkeypatch, "*")
    assert _get(cfg, "127.0.0.1", "") != 403


@pytest.mark.parametrize("door", ["ip", "path"])
@pytest.mark.parametrize("fai", ["*", None])
def test_nginx_edge_forged_leftmost_allowed_hop_is_403(monkeypatch, door, fai) -> None:
    # Validator's case: a public client (198.51.100.7, not allowed) through the
    # loopback nginx edge puts an allow-listed address first. nginx appends the
    # real peer, so the client is the last hop; door=ip and the human Wall ACL
    # both refuse it, with or without uvicorn's env trust (#791 on top of #731).
    monkeypatch.setenv("AGENT_COORD_DOOR", door)
    cfg = _config(monkeypatch, fai)
    assert _get(cfg, "127.0.0.1", f"{ALLOWED}, 198.51.100.7") == 403
    assert _get(cfg, "127.0.0.1", "127.0.0.1, 198.51.100.7") == 403
    assert _get(cfg, "127.0.0.1", f"198.51.100.7, {ALLOWED}") != 403
