# -*- coding: utf-8 -*-
"""Progressive trees #55: depth-cap + limit/cursor + parent_id expand for tree-mail/todo."""
from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from agent_coord.lib.observe import parse_roots
from agent_coord.server.asgi import make_asgi_app
from agent_coord.server.records.floor import (
    LIST_PAGE_DEFAULT,
    TREE_DEPTH_DEFAULT,
    _flatten_trees_stream,
    _tree_stream_cursor_key,
    page_trees_progressive,
    parse_tree_depth,
    parse_tree_parent_id,
    v1_tree_mail,
    v1_tree_todo,
)


def _forest() -> list[dict]:
    """Two forests; nest-set depths 0..2; some leaves, some with children."""
    return [
        {
            "name": "TREE_a",
            "hidden": False,
            "nodes": [
                {
                    "type": "mail",
                    "id": 1,
                    "lft": 1,
                    "rgt": 10,
                    "depth": 0,
                    "title": "root-a",
                    "status": "",
                    "who": "",
                    "roster_id": "demo",
                    "has_children": True,
                },
                {
                    "type": "mail",
                    "id": 2,
                    "lft": 2,
                    "rgt": 7,
                    "depth": 1,
                    "title": "child-a",
                    "status": "",
                    "who": "",
                    "roster_id": "demo",
                    "has_children": True,
                },
                {
                    "type": "mail",
                    "id": 3,
                    "lft": 3,
                    "rgt": 4,
                    "depth": 2,
                    "title": "grand-a",
                    "status": "",
                    "who": "",
                    "roster_id": "demo",
                    "has_children": False,
                },
                {
                    "type": "mail",
                    "id": 4,
                    "lft": 5,
                    "rgt": 6,
                    "depth": 2,
                    "title": "grand-b",
                    "status": "",
                    "who": "",
                    "roster_id": "demo",
                    "has_children": False,
                },
                {
                    "type": "mail",
                    "id": 5,
                    "lft": 8,
                    "rgt": 9,
                    "depth": 1,
                    "title": "child-leaf",
                    "status": "",
                    "who": "",
                    "roster_id": "demo",
                    "has_children": False,
                },
            ],
        },
        {
            "name": "TREE_b",
            "hidden": False,
            "nodes": [
                {
                    "type": "mail",
                    "id": 10,
                    "lft": 1,
                    "rgt": 4,
                    "depth": 0,
                    "title": "root-b",
                    "status": "",
                    "who": "",
                    "roster_id": "demo",
                    "has_children": True,
                },
                {
                    "type": "mail",
                    "id": 11,
                    "lft": 2,
                    "rgt": 3,
                    "depth": 1,
                    "title": "child-b",
                    "status": "",
                    "who": "",
                    "roster_id": "demo",
                    "has_children": False,
                },
            ],
        },
    ]


def test_parse_tree_defaults() -> None:
    assert parse_tree_depth({}) == TREE_DEPTH_DEFAULT == 1
    assert parse_tree_depth({"depth": ["2"]}) == 2
    assert parse_tree_depth({"depth": ["nope"]}) == TREE_DEPTH_DEFAULT
    assert parse_tree_depth({"depth": ["-3"]}) == 0
    assert parse_tree_parent_id({}) is None
    assert parse_tree_parent_id({"parent_id": ["mail:101"]}) == "mail:101"
    assert parse_tree_parent_id({"parent_id": ["  "]}) is None


def test_flatten_depth_cap_and_cursor_key() -> None:
    stream = _flatten_trees_stream(_forest(), depth=1, parent_id=None)
    ids = [(r["_forest"], r["id"], r["depth"]) for r in stream]
    assert ids == [
        ("TREE_a", 1, 0),
        ("TREE_a", 2, 1),
        ("TREE_a", 5, 1),
        ("TREE_b", 10, 0),
        ("TREE_b", 11, 1),
    ]
    assert all("has_children" in r for r in stream)
    assert _tree_stream_cursor_key(stream[1]) == "TREE_a|mail:2|2"


def test_page_trees_progressive_limit_cursor() -> None:
    trees, nxt = page_trees_progressive(_forest(), 2, None, depth=1)
    assert [n["id"] for t in trees for n in t["nodes"]] == [1, 2]
    assert nxt == "TREE_a|mail:2|2"
    trees2, nxt2 = page_trees_progressive(_forest(), 2, nxt, depth=1)
    assert [n["id"] for t in trees2 for n in t["nodes"]] == [5, 10]
    assert nxt2 == "TREE_b|mail:10|1"
    trees3, nxt3 = page_trees_progressive(_forest(), 2, nxt2, depth=1)
    assert [n["id"] for t in trees3 for n in t["nodes"]] == [11]
    assert nxt3 is None
    empty, n0 = page_trees_progressive(_forest(), 2, "missing", depth=1)
    assert empty == [] and n0 is None


def test_page_trees_expand_direct_children_only() -> None:
    trees, nxt = page_trees_progressive(
        _forest(), 50, None, depth=1, parent_id="mail:2"
    )
    assert len(trees) == 1 and trees[0]["name"] == "TREE_a"
    assert [n["id"] for n in trees[0]["nodes"]] == [3, 4]
    assert all(n["depth"] == 2 for n in trees[0]["nodes"])
    assert nxt is None
    # depth-2 grandchildren not returned when expanding root
    trees_r, _ = page_trees_progressive(
        _forest(), 50, None, parent_id="mail:1"
    )
    assert [n["id"] for n in trees_r[0]["nodes"]] == [2, 5]
    bad, nbad = page_trees_progressive(_forest(), 10, None, parent_id="not-an-id")
    assert bad == [] and nbad is None


def test_omit_queries_defaults_progressive_not_full_slice(monkeypatch) -> None:
    monkeypatch.setattr(
        "agent_coord.server.records.floor.build_trees_typed",
        lambda cn, want, typ, aff: _forest(),
    )
    monkeypatch.setattr(
        "agent_coord.server.records.floor._v1_project_scope",
        lambda project=None, projects=None: (["PROJ_demo"], {"demo"}),
    )
    monkeypatch.setattr(
        "agent_coord.server.records.floor._v1_aff_ids",
        lambda cn, want: None,
    )
    out = v1_tree_mail(object(), project="demo")
    assert out["next"] is not None or True  # small forest may exhaust
    ids = [n["id"] for t in out["trees"] for n in t["nodes"]]
    # depth<=1 stream has 5 nodes; default limit 50 keeps all depth-capped, not depth-2
    assert 3 not in ids and 4 not in ids
    assert ids == [1, 2, 5, 10, 11]
    assert out["next"] is None
    assert all("has_children" in n for t in out["trees"] for n in t["nodes"])
    assert LIST_PAGE_DEFAULT == 50


def test_v1_tree_todo_pages(monkeypatch) -> None:
    todo_forest = [
        {
            "name": "TREE_t",
            "hidden": False,
            "nodes": [
                {
                    "type": "todo",
                    "id": i,
                    "lft": i,
                    "rgt": i + 1 if i > 1 else 20,
                    "depth": 0 if i == 1 else 1,
                    "title": f"t{i}",
                    "status": "open",
                    "who": "",
                    "roster_id": "demo",
                    "has_children": i == 1,
                }
                for i in range(1, 6)
            ],
        }
    ]
    # fix nest-set on root
    todo_forest[0]["nodes"][0]["rgt"] = 12

    monkeypatch.setattr(
        "agent_coord.server.records.floor.build_trees_typed",
        lambda cn, want, typ, aff: todo_forest,
    )
    monkeypatch.setattr(
        "agent_coord.server.records.floor._v1_project_scope",
        lambda project=None, projects=None: (["PROJ_demo"], {"demo"}),
    )
    monkeypatch.setattr(
        "agent_coord.server.records.floor._v1_aff_ids",
        lambda cn, want: None,
    )
    out = v1_tree_todo(object(), project="demo", limit=2, depth=1)
    assert [n["id"] for t in out["trees"] for n in t["nodes"]] == [1, 2]
    assert out["next"] == "TREE_t|todo:2|2"
    out2 = v1_tree_todo(object(), project="demo", limit=2, cursor=out["next"], depth=1)
    assert [n["id"] for t in out2["trees"] for n in t["nodes"]] == [3, 4]
    assert out2["next"] == "TREE_t|todo:4|4"


def _client(monkeypatch) -> TestClient:
    monkeypatch.setattr("agent_coord.server.admin.door.mode", lambda: "path")
    monkeypatch.setattr("agent_coord.server.allow.allowed", lambda *a, **k: True)
    root = Path(__file__).resolve().parents[2]
    app = make_asgi_app(parse_roots(cwd=root), api_only=True)
    return TestClient(app)


def test_middleware_passes_tree_page_kwargs(monkeypatch) -> None:
    seen: dict = {}

    def _mail(cn, **k):
        seen.clear()
        seen.update(k)
        return {
            "at": "t",
            "node": "n",
            "version": "0.5.8",
            "parts": ["trees"],
            "trees": [],
            "next": None,
            "mill": "0.5.8",
        }

    monkeypatch.setattr("agent_coord.server.records.floor.v1_tree_mail", _mail)

    class _C:
        _cn = object()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr("agent_coord.server.middleware._office", lambda: _C())
    client = _client(monkeypatch)
    r = client.get(
        "/api/v1/tree-mail?project=demo&limit=10&depth=1&parent_id=mail:2&cursor=TREE_a%7Cmail:2%7C2"
    )
    assert r.status_code == 200
    assert seen["limit"] == 10
    assert seen["depth"] == 1
    assert seen["parent_id"] == "mail:2"
    assert seen["cursor"] == "TREE_a|mail:2|2"
    assert "next" in r.json()
