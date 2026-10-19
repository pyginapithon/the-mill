# -*- coding: utf-8 -*-
"""The floor bundle route is gone. A glance with no project still refuses the book."""
from pathlib import Path

from fastapi.testclient import TestClient

from agent_coord.lib.observe import parse_roots
from agent_coord.server.asgi import make_asgi_app


def test_floor_route_is_gone(monkeypatch) -> None:
    def boom(*a, **k):
        raise AssertionError("floor must not query the book")

    monkeypatch.setattr("agent_coord.server.records.floor.floor", boom)
    monkeypatch.setattr("agent_coord.server.admin.door.mode", lambda: "path")
    monkeypatch.setattr("agent_coord.server.allow.allowed", lambda *a, **k: True)
    root = Path(__file__).resolve().parents[2]
    app = make_asgi_app(parse_roots(cwd=root), api_only=True)
    client = TestClient(app)
    bare = client.get("/api/floor")
    assert bare.status_code == 404
    glance = client.get("/api/office-glance")
    assert glance.status_code == 400
    assert "project" in glance.json()["error"]
