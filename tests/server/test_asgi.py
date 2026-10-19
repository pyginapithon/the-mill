# -*- coding: utf-8 -*-
"""Unit: FastAPI mill-wall hosts the same Handler (mirrors agent_coord/server)."""
from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from agent_coord.lib.observe import parse_roots
from agent_coord.server.asgi import make_asgi_app


def test_asgi_board_and_howto() -> None:
    here = Path(__file__).resolve().parents[2]
    app = make_asgi_app(parse_roots(cwd=here), api_only=False)
    client = TestClient(app)
    r = client.get("/")
    assert r.status_code == 200
    assert "charset=utf-8" in (r.headers.get("content-type") or "").lower()
    assert b"THE MILL" in r.content
    assert r.headers.get("x-mill-duration-ms")
    how = client.get("/api/howto")
    assert how.status_code == 200
    body = how.json()
    assert body.get("api") == "1"


def test_browser_miss_is_an_error_page(monkeypatch) -> None:
    monkeypatch.setattr("agent_coord.server.admin.door.mode", lambda: "invite")
    here = Path(__file__).resolve().parents[2]
    app = make_asgi_app(parse_roots(cwd=here), api_only=False)
    client = TestClient(app)
    page = client.get("/", headers={"Accept": "text/html"})
    assert page.status_code == 404
    assert "text/html" in (page.headers.get("content-type") or "")
    assert b"This address is not open" in page.content
    assert b"THE MILL" in page.content
    plain = client.get("/")
    assert plain.status_code == 404
    assert plain.content == b"not found\n"
    missing = client.get("/no-such-page", headers={"Accept": "text/html"})
    assert missing.status_code == 404
    assert b"This address is not open" in missing.content
    api = client.get("/api/no-such", headers={"Accept": "text/html"})
    assert api.status_code == 404
    assert api.content == b"not found\n"
    icon = client.get("/favicon.svg")
    assert icon.status_code == 200
    assert b"<svg" in icon.content


def test_browser_unknown_page_when_door_is_open(monkeypatch) -> None:
    monkeypatch.setattr("agent_coord.server.admin.door.mode", lambda: "path")
    here = Path(__file__).resolve().parents[2]
    app = make_asgi_app(parse_roots(cwd=here), api_only=False)
    client = TestClient(app)
    page = client.get("/no-such-page", headers={"Accept": "text/html"})
    assert page.status_code == 404
    assert b"That page is not here" in page.content


def test_asgi_archaic_glance_gone() -> None:
    """Archaic glance paths are gone; /api/events aliases v1 (needs ?project=)."""
    here = Path(__file__).resolve().parents[2]
    app = make_asgi_app(parse_roots(cwd=here), api_only=False)
    client = TestClient(app)
    for path in ("/api/spend", "/api/issues", "/api/presence"):
        r = client.get(path)
        assert r.status_code == 404, path
    # Live contract: /api/events -> same as /api/v1/events (400 without project)
    ev = client.get("/api/events")
    assert ev.status_code == 400
    assert "project" in (ev.text or "").lower()
    v1 = client.get("/api/v1/events")
    assert v1.status_code == 400


def test_nest_path_spa_serves_board() -> None:
    """Hub SPA fallthrough: Nest path families serve the same board as /."""
    here = Path(__file__).resolve().parents[2]
    app = make_asgi_app(parse_roots(cwd=here), api_only=False)
    client = TestClient(app)
    root = client.get("/")
    assert root.status_code == 200
    assert "text/html" in (root.headers.get("content-type") or "")
    assert b"THE MILL" in root.content
    for path in (
        "/project",
        "/project/the-mill",
        "/station",
        "/station/192.0.2.10",
        "/role",
        "/role/Admin",
        "/board",
        "/welcome",
    ):
        page = client.get(path)
        assert page.status_code == 200, path
        assert "text/html" in (page.headers.get("content-type") or ""), path
        assert b"THE MILL" in page.content, path
    # Boundary: prefix without slash separator must not match
    for miss_path in (
        "/projectfoo",
        "/projects",
        "/projects/the-mill",
        "/stations/192.0.2.10",
        "/roles/Admin",
        "/stationfoo",
        "/rolefoo",
    ):
        miss = client.get(miss_path, headers={"Accept": "text/html"})
        assert miss.status_code == 404, miss_path
    # API must not fall through to board HTML
    api = client.get("/api/howto")
    assert api.status_code == 200
    assert "application/json" in (api.headers.get("content-type") or "")
    assert b"THE MILL" not in api.content


def test_nest_path_spa_api_only_blocks_board(monkeypatch) -> None:
    monkeypatch.setattr("agent_coord.server.admin.door.mode", lambda: "path")
    here = Path(__file__).resolve().parents[2]
    app = make_asgi_app(parse_roots(cwd=here), api_only=True)
    client = TestClient(app)
    for path in ("/project/the-mill", "/station/192.0.2.10", "/role/Admin"):
        page = client.get(path, headers={"Accept": "text/html"})
        assert page.status_code == 404, path
        assert b"API only" in page.content or b"api only" in page.content, path


def test_root_domain_js_is_javascript_not_board() -> None:
    """Root /mail|/score|/todo/*.js must be JS (Hub static), never Nest board HTML."""
    here = Path(__file__).resolve().parents[2]
    app = make_asgi_app(parse_roots(cwd=here), api_only=False)
    client = TestClient(app)
    for path in ("/mail/mail.js", "/score/score.js", "/todo/todo.js", "/lib/lazy.js", "/boot.js"):
        r = client.get(path)
        assert r.status_code == 200, path
        ct = (r.headers.get("content-type") or "").lower()
        assert "javascript" in ct, (path, ct)
        assert b"<!DOCTYPE html>" not in r.content[:200].upper() and b"<html" not in r.content[:200].lower(), path


def test_nest_spa_does_not_catch_domain_js() -> None:
    """Stale relative mail/mail.js under /project/... must not return board HTML."""
    here = Path(__file__).resolve().parents[2]
    app = make_asgi_app(parse_roots(cwd=here), api_only=False)
    client = TestClient(app)
    for path in (
        "/project/finance/mail/mail.js",
        "/project/finance/score/score.js",
        "/project/finance/todo/todo.js",
        "/station/192.0.2.10/mail/mail.js",
    ):
        r = client.get(path)
        ct = (r.headers.get("content-type") or "").lower()
        # Prefer 404; never Nest board HTML (Unexpected token '<').
        assert "text/html" not in ct or b"THE MILL" not in r.content, (path, r.status_code, ct)
        assert r.status_code != 200 or "javascript" in ct or r.status_code == 404, (
            path,
            r.status_code,
            ct,
        )

