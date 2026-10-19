# -*- coding: utf-8 -*-
"""Role and station on /api/v1 part routes. /api/floor is gone."""
from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from agent_coord.lib.observe import parse_roots
from agent_coord.server.asgi import make_asgi_app
from agent_coord.server.records.floor import v1_by_scope
import agent_coord.server.middleware as mw


def _view() -> dict:
    return {
        "agents": [{"owner": "a1"}, {"owner": "a2"}, {"id": "a3", "owner": "a3"}],
        "mailbox": [
            {"id": 5, "dst": "DESK_b"},
            {"id": 4, "dst": "DESK_b"},
            {"id": 3, "dst": "DESK_c"},
        ],
        "desk_unread": {"DESK_b": 2, "DESK_c": 1},
        "needs": [{"id": 11}, {"id": 10}, {"id": 9}],
        "issues": [{"id": 8}, {"id": 7}],
        "kpis": [
            {"owner": "o1", "kpi": "k", "roster_id": "a"},
            {"owner": "o2", "kpi": "k", "roster_id": "a"},
        ],
        "locks": [
            {"resource": "r1", "owner": "o", "roster_id": "a"},
            {"resource": "r2", "owner": "o", "roster_id": "a"},
        ],
        "events": [
            {"type": "todo", "id": 1},
            {"type": "todo", "id": 2},
            {"type": "mail", "id": 3},
        ],
        "fp": {"agents": "aa", "mail": "bb"},
    }


def test_v1_by_scope_pages_a_role(monkeypatch) -> None:
    calls: list[tuple] = []

    def _scope(cn, kind, ident, parts, client_fps=None, **k):
        calls.append((kind, ident, list(parts or [])))
        return _view()

    monkeypatch.setattr("agent_coord.server.records.floor.floor_scope", _scope)
    agents = v1_by_scope(object(), "agents", "role", "Admin", limit=2)
    assert [a["id"] for a in agents["agents"]] == ["a1", "a2"]
    assert agents["next"] == "a2"
    assert agents["fp"]["agents"] == "aa"
    assert calls == [("role", "Admin", ["agents"])]

    mail = v1_by_scope(object(), "mailbox", "role", "Admin", limit=2)
    assert [m["id"] for m in mail["mailbox"]] == [5, 4]
    assert mail["desk_unread"] == {"DESK_b": 2, "DESK_c": 1}
    assert mail["next"] == "4"

    todos = v1_by_scope(object(), "todos", "lan", "192.0.2.10", limit=2)
    assert [c["id"] for c in todos["needs"]] == [11, 10]
    assert todos["issues"] == []
    assert todos["next"] == "10"
    assert calls[-1] == ("lan", "192.0.2.10", ["todos"])

    scores = v1_by_scope(object(), "scores", "role", "Admin", limit=1)
    assert scores["kpis"][0]["id"] == "o1|k|a"
    holds = v1_by_scope(object(), "holds", "role", "Admin", limit=1)
    assert holds["locks"][0]["id"] == "r1|o|a"
    events = v1_by_scope(object(), "events", "role", "Admin", limit=2)
    assert events["next"] == "todo:2"

    mapped = v1_by_scope(object(), "map", "role", "Admin", limit=2)
    assert [a["id"] for a in mapped["agents"]] == ["a1", "a2"]
    assert [m["id"] for m in mapped["mailbox"]] == [5, 4]
    assert mapped["desk_unread"]["DESK_c"] == 1

    empty_tl = v1_by_scope(object(), "timeline", "role", "Admin", parts=["timeline"], limit=2)
    assert empty_tl["timeline"] == []
    assert [a["id"] for a in empty_tl["agents"]] == ["a1", "a2"]
    assert calls[-1][2] == ["agents"]

    timed = v1_by_scope(object(), "timeline", "role", "Admin", parts=["events"], limit=2)
    assert [e["id"] for e in timed["events"]] == [1, 2]
    assert calls[-1][2] == ["agents", "events"]


def test_v1_by_scope_empty_parts_skip_the_book(monkeypatch) -> None:
    def _scope(*a, **k):
        raise AssertionError("rooms, trees, and watchers do not read the role book")

    monkeypatch.setattr("agent_coord.server.records.floor.floor_scope", _scope)
    seen: dict = {}

    def _names(cn, **k):
        seen.update(k)
        return {"catalog": [{"kind": "role", "name": "Admin"}], "next": None}

    monkeypatch.setattr("agent_coord.server.records.floor.v1_names", _names)
    names = v1_by_scope(object(), "names", "role", "Admin", limit=2)
    assert names["catalog"][0]["name"] == "Admin"
    assert "project" not in seen
    rooms = v1_by_scope(object(), "rooms", "role", "Admin")
    assert rooms["trees"] == []
    assert v1_by_scope(object(), "tree-mail", "lan", "192.0.2.11")["trees"] == []
    assert v1_by_scope(object(), "watchers", "role", "Admin")["watchers"] == []


def test_v1_role_and_lan_http(monkeypatch) -> None:
    monkeypatch.setattr("agent_coord.server.admin.door.mode", lambda: "path")
    monkeypatch.setattr("agent_coord.server.allow.allowed", lambda *a, **k: True)

    class _C:
        _cn = object()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr("agent_coord.server.middleware._office", lambda: _C())
    mw._floor_cache.clear()
    mw._floor_flight.clear()
    seen: dict[str, list] = {"scope": [], "agents": []}

    def _by_scope(cn, route, kind, ident, client_fps=None, *, limit=None, cursor=None, parts=None):
        seen["scope"].append((route, kind, ident, limit, cursor))
        return {"at": "t", "parts": ["agents"], "agents": [{"id": ident}], "next": None}

    def _agents(cn, **k):
        seen["agents"].append(k)
        return {"at": "t", "parts": ["agents"], "agents": [{"id": "proj"}], "next": None}

    monkeypatch.setattr("agent_coord.server.records.floor.v1_by_scope", _by_scope)
    monkeypatch.setattr("agent_coord.server.records.floor.v1_agents", _agents)
    root = Path(__file__).resolve().parents[2]
    client = TestClient(make_asgi_app(parse_roots(cwd=root), api_only=True))

    role = client.get("/api/v1/agents?role=Admin&limit=2")
    assert role.status_code == 200
    assert role.json()["agents"][0]["id"] == "Admin"
    assert seen["scope"][-1] == ("agents", "role", "Admin", 2, None)

    lan = client.get("/api/v1/agents?lan=192.0.2.10")
    assert lan.status_code == 200
    assert seen["scope"][-1][1:] == ("lan", "192.0.2.10", 50, None)

    project = client.get("/api/v1/agents?project=scope-keep&limit=4")
    assert project.status_code == 200
    assert seen["agents"][0]["projects"] == ["scope-keep"]
    assert seen["agents"][0]["limit"] == 4
    assert len(seen["scope"]) == 2

    again = client.get("/api/v1/agents?role=Admin&limit=2")
    assert again.status_code == 200
    assert len(seen["scope"]) == 2

    both = client.get("/api/v1/agents?project=scope-keep&role=Admin")
    assert both.status_code == 400
    assert both.json()["error"] == "GET /api/v1/agents requires one of ?project= or ?role= or ?lan="
    missing = client.get("/api/v1/agents")
    assert missing.status_code == 400
    pair = client.get("/api/v1/mailbox?role=Admin&lan=192.0.2.10")
    assert pair.status_code == 400

    gone = client.get("/api/floor?project=Office&parts=agents")
    assert gone.status_code == 404
