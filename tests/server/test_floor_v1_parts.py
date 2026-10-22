# -*- coding: utf-8 -*-
"""GET /api/v1/{rooms,mailbox,tree-mail,tree-todo,todos,agents,scores,holds,watchers,events,names} measure isolates."""
from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from agent_coord.lib.observe import parse_roots
from agent_coord.server.asgi import make_asgi_app
from agent_coord.server.records.floor import (
    _v1_project_scope,
    build_rooms,
    build_trees_typed,
)


def _client(monkeypatch) -> TestClient:
    monkeypatch.setattr("agent_coord.server.admin.door.mode", lambda: "path")
    monkeypatch.setattr("agent_coord.server.allow.allowed", lambda *a, **k: True)
    root = Path(__file__).resolve().parents[2]
    app = make_asgi_app(parse_roots(cwd=root), api_only=True)
    return TestClient(app)


def test_v1_requires_project(monkeypatch) -> None:
    client = _client(monkeypatch)
    for path in (
        "/api/v1/rooms",
        "/api/v1/mailbox",
        "/api/v1/tree-mail",
        "/api/v1/tree-todo",
        "/api/v1/todos",
        "/api/v1/agents",
        "/api/v1/scores",
        "/api/v1/holds",
        "/api/v1/watchers",
        "/api/v1/events",
        "/api/v1/names",
    ):
        r = client.get(path)
        assert r.status_code == 400, path
        assert "project" in r.json()["error"]
        assert "mill" in r.json()


def test_v1_routes_return_mill_and_parts(monkeypatch) -> None:
    monkeypatch.setattr(
        "agent_coord.server.records.floor.v1_rooms",
        lambda cn, **k: {"at": "t", "node": "n", "version": "0.5.6", "parts": ["rooms"], "trees": []},
    )
    monkeypatch.setattr(
        "agent_coord.server.records.floor.v1_mailbox",
        lambda cn, **k: {
            "at": "t",
            "node": "n",
            "version": "0.5.6",
            "parts": ["mail"],
            "mailbox": [{"id": 1}],
            "desk_unread": {"a": 1},
            "fp": {"mail": "0123456789abcdef"},
        },
    )
    monkeypatch.setattr(
        "agent_coord.server.records.floor.v1_tree_mail",
        lambda cn, **k: {"at": "t", "node": "n", "version": "0.5.6", "parts": ["trees"], "trees": [{"name": "TREE_x", "nodes": [{"type": "mail"}]}]},
    )
    monkeypatch.setattr(
        "agent_coord.server.records.floor.v1_tree_todo",
        lambda cn, **k: {"at": "t", "node": "n", "version": "0.5.6", "parts": ["trees"], "trees": [{"name": "TREE_y", "nodes": [{"type": "todo"}]}]},
    )
    monkeypatch.setattr(
        "agent_coord.server.records.floor.v1_todos",
        lambda cn, **k: {
            "at": "t",
            "node": "n",
            "version": "0.5.6",
            "parts": ["todos"],
            "needs": [{"id": 2}],
            "issues": [],
            "fp": {"todos": "fedcba9876543210"},
        },
    )
    monkeypatch.setattr(
        "agent_coord.server.records.floor.v1_agents",
        lambda cn, **k: {
            "at": "t",
            "node": "n",
            "version": "0.5.6",
            "parts": ["agents"],
            "agents": [{"id": "desk_a", "owner": "desk_a"}],
            "next": None,
            "fp": {"agents": "1122334455667788"},
        },
    )
    monkeypatch.setattr(
        "agent_coord.server.records.floor.v1_scores",
        lambda cn, **k: {
            "at": "t",
            "node": "n",
            "version": "0.5.6",
            "parts": ["scores"],
            "kpis": [{"id": "o|k|a", "owner": "o", "kpi": "k"}],
            "next": None,
            "fp": {"scores": "9988776655443322"},
        },
    )
    monkeypatch.setattr(
        "agent_coord.server.records.floor.v1_holds",
        lambda cn, **k: {
            "at": "t",
            "node": "n",
            "version": "0.5.6",
            "parts": ["holds"],
            "locks": [{"id": "res|own|aff", "resource": "res", "owner": "own"}],
            "next": None,
            "fp": {"holds": "aabbccddeeff0011"},
        },
    )
    monkeypatch.setattr(
        "agent_coord.server.records.floor.v1_watchers",
        lambda cn, **k: {
            "at": "t",
            "node": "n",
            "version": "0.5.6",
            "parts": ["watchers"],
            "watchers": [{"type": "todo", "id": 3, "title": "t"}],
            "next": None,
            "fp": {"watchers": "ffeeddccbbaa9988"},
        },
    )
    monkeypatch.setattr(
        "agent_coord.server.records.floor.v1_events",
        lambda cn, **k: {
            "at": "t",
            "node": "n",
            "version": "0.5.6",
            "parts": ["events"],
            "events": [{"type": "todo", "id": 7, "kind": "todo"}],
            "next": None,
            "fp": {"events": "1122334455667788"},
        },
    )
    monkeypatch.setattr(
        "agent_coord.server.records.floor.v1_names",
        lambda cn, **k: {
            "at": "t",
            "node": "n",
            "version": "0.5.6",
            "parts": ["names"],
            "catalog": [{"kind": "project", "name": "demo", "deleted": False}],
            "next": None,
            "fp": {"names": "2233445566778899"},
        },
    )
    # Book open still happens; stub the office context to avoid MySQL.
    class _C:
        _cn = object()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr("agent_coord.server.middleware._office", lambda: _C())
    client = _client(monkeypatch)

    rooms = client.get("/api/v1/rooms?project=the-mill")
    assert rooms.status_code == 200
    body = rooms.json()
    assert body["mill"]
    assert body["parts"] == ["rooms"]
    assert "trees" in body
    assert "timings" not in body

    timed = client.get("/api/v1/rooms?project=the-mill&timings=1")
    assert timed.status_code == 200
    tb = timed.json()
    assert "timings" in tb
    assert "sql_ms" in tb["timings"]
    assert "resp_b" in tb["timings"]
    assert tb["timings"]["n"] == 0

    mail = client.get("/api/v1/mailbox?project=demo")
    assert mail.status_code == 200
    assert mail.json()["mailbox"][0]["id"] == 1
    assert mail.json()["fp"]["mail"] == "0123456789abcdef"

    tm = client.get("/api/v1/tree-mail?project=demo")
    assert tm.status_code == 200
    assert tm.json()["trees"][0]["nodes"][0]["type"] == "mail"

    tt = client.get("/api/v1/tree-todo?project=demo")
    assert tt.status_code == 200
    assert tt.json()["trees"][0]["nodes"][0]["type"] == "todo"

    todos = client.get("/api/todos?project=demo")  # rewrite alias path
    assert todos.status_code == 200
    assert todos.json()["needs"][0]["id"] == 2

    agents = client.get("/api/v1/agents?project=demo")
    assert agents.status_code == 200
    ab = agents.json()
    assert ab["parts"] == ["agents"]
    assert ab["agents"][0]["owner"] == "desk_a"
    assert ab["fp"]["agents"] == "1122334455667788"

    scores = client.get("/api/v1/scores?project=demo")
    assert scores.status_code == 200
    sb = scores.json()
    assert sb["parts"] == ["scores"]
    assert sb["kpis"][0]["kpi"] == "k"
    assert sb["fp"]["scores"] == "9988776655443322"

    holds = client.get("/api/v1/holds?project=demo")
    assert holds.status_code == 200
    hb = holds.json()
    assert hb["parts"] == ["holds"]
    assert hb["locks"][0]["resource"] == "res"
    assert hb["fp"]["holds"] == "aabbccddeeff0011"

    watchers = client.get("/api/v1/watchers?project=demo")
    assert watchers.status_code == 200
    wb = watchers.json()
    assert wb["parts"] == ["watchers"]
    assert wb["watchers"][0]["type"] == "todo"
    assert wb["fp"]["watchers"] == "ffeeddccbbaa9988"

    events = client.get("/api/v1/events?project=demo")
    assert events.status_code == 200
    eb = events.json()
    assert eb["parts"] == ["events"]
    assert eb["events"][0]["id"] == 7
    assert eb["fp"]["events"] == "1122334455667788"

    names = client.get("/api/v1/names?project=demo")
    assert names.status_code == 200
    nb = names.json()
    assert nb["parts"] == ["names"]
    assert nb["catalog"][0]["name"] == "demo"
    assert nb["fp"]["names"] == "2233445566778899"


def test_floor_route_is_gone(monkeypatch) -> None:
    def boom(*a, **k):
        raise AssertionError("floor must not query")

    monkeypatch.setattr("agent_coord.server.records.floor.floor", boom)
    client = _client(monkeypatch)
    bare = client.get("/api/floor")
    assert bare.status_code == 404


def test_v1_project_scope_slugs() -> None:
    ps, want = _v1_project_scope(project="the-mill")
    assert ps == ["the-mill"]
    assert "the-mill" in want


def test_build_rooms_lean_no_body(monkeypatch) -> None:
    monkeypatch.setattr(
        "agent_coord.server.records.tree.mail_room_root_rows",
        lambda cn, aff: [
            {"tree": "TREE_room1", "type": "mail", "id": 9, "lft": 1, "rgt": 4, "roster_id": 1},
        ],
    )
    monkeypatch.setattr(
        "agent_coord.server.records.name.select",
        lambda cn, **k: [{"id": 1, "name": "PROJ_demo"}],
    )
    trees = build_rooms(object(), want={"demo"})
    assert len(trees) == 1
    node = trees[0]["nodes"][0]
    assert node["type"] == "mail"
    assert node["lft"] == 1
    assert node["title"] == ""
    assert "body" not in node


def test_build_trees_typed_filters(monkeypatch) -> None:
    monkeypatch.setattr(
        "agent_coord.server.records.tree.mail_forest_rows",
        lambda cn, aff=None: [],
    )
    monkeypatch.setattr(
        "agent_coord.server.records.tree.todo_forest_rows",
        lambda cn, aff=None: [],
    )
    monkeypatch.setattr(
        "agent_coord.server.records.floor._floor_trees",
        lambda *a, **k: [
            {
                "name": "TREE_mix",
                "hidden": False,
                "nodes": [
                    {"type": "name", "id": 9, "lft": 1, "rgt": 8, "depth": 0},
                    {"type": "mail", "id": 1, "lft": 2, "rgt": 5, "depth": 1},
                    {"type": "mail", "id": 4, "lft": 3, "rgt": 4, "depth": 2},
                    {"type": "todo", "id": 2, "lft": 6, "rgt": 7, "depth": 1},
                ],
            }
        ],
    )
    monkeypatch.setattr(
        "agent_coord.server.records.name.select",
        lambda cn, **k: [],
    )
    mail_only = build_trees_typed(object(), None, "mail", None)
    assert len(mail_only) == 1
    assert [n["id"] for n in mail_only[0]["nodes"]] == [1, 4]
    assert [n["depth"] for n in mail_only[0]["nodes"]] == [0, 1]
    assert mail_only[0]["nodes"][0]["has_children"] is True
    assert mail_only[0]["nodes"][1]["has_children"] is False
    todo_only = build_trees_typed(object(), None, "todo", None)
    assert [n["type"] for n in todo_only[0]["nodes"]] == ["todo"]
    assert todo_only[0]["nodes"][0]["depth"] == 0
    assert todo_only[0]["nodes"][0]["has_children"] is False


def test_build_trees_typed_mail_returns_whole_tree(monkeypatch) -> None:
    """A page that includes the tree gets every letter, each with its roster."""
    monkeypatch.setattr(
        "agent_coord.server.records.tree.mail_forest_rows",
        lambda cn, aff: [
            {
                "tree": "room",
                "type": "mail",
                "id": 1,
                "lft": 1,
                "rgt": 6,
                "roster_id": 1,
                "mail_body": "first",
                "mail_src": "a",
            },
            {
                "tree": "room",
                "type": "mail",
                "id": 2,
                "lft": 2,
                "rgt": 5,
                "roster_id": 2,
                "mail_body": "second",
                "mail_src": "b",
            },
            {
                "tree": "room",
                "type": "mail",
                "id": 3,
                "lft": 3,
                "rgt": 4,
                "roster_id": 3,
                "mail_body": "third",
                "mail_src": "c",
            },
        ],
    )
    monkeypatch.setattr(
        "agent_coord.server.records.name.select",
        lambda cn, **k: [
            {"id": 1, "name": "Office"},
            {"id": 2, "name": "the-mill"},
            {"id": 3, "name": "other"},
        ],
    )
    office = build_trees_typed(object(), {"Office"}, "mail", [1])
    mill = build_trees_typed(object(), {"the-mill"}, "mail", [2])
    other = build_trees_typed(object(), {"other"}, "mail", [3])
    assert [n["id"] for n in office[0]["nodes"]] == [1, 2, 3]
    assert [n["id"] for n in mill[0]["nodes"]] == [1, 2, 3]
    assert [n["id"] for n in other[0]["nodes"]] == [1, 2, 3]
    assert [n["roster_id"] for n in office[0]["nodes"]] == [
        "Office",
        "the-mill",
        "other",
    ]

def test_v1_envelope_parts() -> None:
    from agent_coord.server.records.floor import _v1_envelope

    env = _v1_envelope(["rooms"])
    assert env["parts"] == ["rooms"]
    assert "at" in env
    assert "version" in env
    assert env.get("trust") in ("high", "limited")


def test_build_rooms_lists_every_room_672(monkeypatch) -> None:
    """#672 S-3: every room at every trust level; ?desk=/scope=membership no longer filter."""
    monkeypatch.setattr(
        "agent_coord.server.records.tree.mail_room_root_rows",
        lambda cn, aff: [
            {"tree": "TREE_in", "type": "mail", "id": 10, "lft": 1, "rgt": 2, "roster_id": 1},
            {"tree": "TREE_out", "type": "mail", "id": 20, "lft": 1, "rgt": 2, "roster_id": 1},
        ],
    )
    monkeypatch.setattr(
        "agent_coord.server.records.name.select",
        lambda cn, **k: [{"id": 1, "name": "PROJ_demo"}],
    )
    from agent_coord.server.records import floor

    assert {t["name"] for t in build_rooms(object(), want={"demo"})} >= {"TREE_in", "TREE_out"}
    for trust in ("limited", "high"):
        monkeypatch.setattr("agent_coord.config.mill_trust", lambda t=trust: t)
        for scope in (None, "membership"):
            out = floor.v1_rooms(object(), projects=["demo"], desk="alice", scope=scope)
            assert {t["name"] for t in out["trees"]} >= {"TREE_in", "TREE_out"}, (trust, scope)
            assert "scope" not in out


def test_multi_project_scope() -> None:
    from agent_coord.server.records.floor import _v1_project_scope

    ps, want = _v1_project_scope(projects=["a", "b"])
    assert ps == ["a", "b"]
    assert "a" in want and "b" in want
