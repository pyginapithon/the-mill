# -*- coding: utf-8 -*-
"""Floor parts + /api/activity limit/cursor paging (#49-54). Trees PARK."""
from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from agent_coord.lib.observe import board_view, parse_roots
from agent_coord.server.asgi import make_asgi_app
from agent_coord.server.records.floor import (
    apply_floor_list_page,
    page_activity_rows,
    page_by_cursor,
)


def test_page_by_cursor_get_key_events() -> None:
    rows = [
        {"type": "mail", "id": 5},
        {"type": "todo", "id": 5},
        {"type": "mail", "id": 4},
    ]
    p1, n1 = page_by_cursor(rows, 1, None, get_key=lambda r: f"{r['type']}:{r['id']}")
    assert p1 == [{"type": "mail", "id": 5}] and n1 == "mail:5"
    p2, n2 = page_by_cursor(rows, 1, n1, get_key=lambda r: f"{r['type']}:{r['id']}")
    assert p2 == [{"type": "todo", "id": 5}] and n2 == "todo:5"


def test_apply_floor_list_page_agents_scores_holds() -> None:
    out = {
        "mailbox": [],
        "needs": [],
        "issues": [],
        "agents": [{"owner": f"d{i}"} for i in range(1, 6)],
        "kpis": [
            {"owner": "a", "kpi": f"k{i}", "roster_id": "p"} for i in range(1, 5)
        ],
        "locks": [
            {"resource": f"r{i}", "owner": "a", "roster_id": "p"} for i in range(1, 4)
        ],
        "watchers": [],
        "events": [],
    }
    apply_floor_list_page(out, limit=2, cursor=None, partset={"agents"})
    assert len(out["agents"]) == 2
    assert out["agents"][0]["id"] == "d1"
    assert out["next"] == "d2"
    out_a2 = {
        "mailbox": [],
        "needs": [],
        "issues": [],
        "agents": [{"owner": f"d{i}", "id": f"d{i}"} for i in range(1, 6)],
        "kpis": [],
        "locks": [],
        "watchers": [],
        "events": [],
    }
    apply_floor_list_page(out_a2, limit=2, cursor="d2", partset={"agents"})
    assert [a["id"] for a in out_a2["agents"]] == ["d3", "d4"]
    assert out_a2["next"] == "d4"
    out2 = {
        "mailbox": [],
        "needs": [],
        "issues": [],
        "agents": [],
        "kpis": [
            {"owner": "a", "kpi": f"k{i}", "roster_id": "p"} for i in range(1, 5)
        ],
        "locks": [],
        "watchers": [],
        "events": [],
    }
    apply_floor_list_page(out2, limit=2, cursor=None, partset={"scores"})
    assert len(out2["kpis"]) == 2 and out2["next"] == "a|k2|p"
    out3 = {
        "mailbox": [],
        "needs": [],
        "issues": [],
        "agents": [],
        "kpis": [],
        "locks": [
            {"resource": f"r{i}", "owner": "a", "roster_id": "p"} for i in range(1, 4)
        ],
        "watchers": [],
        "events": [],
    }
    apply_floor_list_page(out3, limit=2, cursor=None, partset={"holds"})
    assert len(out3["locks"]) == 2 and out3["next"] == "r2|a|p"


def test_apply_floor_list_page_mail_todos_events_watchers() -> None:
    out = {
        "mailbox": [{"id": i} for i in range(5, 0, -1)],
        "needs": [{"id": i} for i in (11, 10, 9)],
        "issues": [{"id": i} for i in (8, 7)],
        "agents": [],
        "kpis": [],
        "locks": [],
        "watchers": [{"type": "mail", "id": i} for i in (3, 2, 1)],
        "events": [
            {"type": "mail", "id": 9},
            {"type": "todo", "id": 9},
            {"type": "join", "id": 1},
        ],
    }
    apply_floor_list_page(out, limit=2, cursor=None, partset={"mail"})
    assert [m["id"] for m in out["mailbox"]] == [5, 4] and out["next"] == "4"

    out_t = {
        "mailbox": [],
        "needs": [{"id": i} for i in (11, 10, 9)],
        "issues": [{"id": i} for i in (8, 7)],
        "agents": [],
        "kpis": [],
        "locks": [],
        "watchers": [],
        "events": [],
    }
    apply_floor_list_page(out_t, limit=2, cursor="10", partset={"todos"})
    assert [c["id"] for c in out_t["needs"]] == [9]
    assert [c["id"] for c in out_t["issues"]] == [8]
    assert out_t["next"] == "8"

    out_e = {
        "mailbox": [],
        "needs": [],
        "issues": [],
        "agents": [],
        "kpis": [],
        "locks": [],
        "watchers": [],
        "events": [
            {"type": "mail", "id": 9},
            {"type": "todo", "id": 9},
            {"type": "join", "id": 1},
        ],
    }
    apply_floor_list_page(out_e, limit=1, cursor=None, partset={"events"})
    assert out_e["events"][0]["type"] == "mail" and out_e["next"] == "mail:9"
    out_e2 = {
        "mailbox": [],
        "needs": [],
        "issues": [],
        "agents": [],
        "kpis": [],
        "locks": [],
        "watchers": [],
        "events": [
            {"type": "mail", "id": 9},
            {"type": "todo", "id": 9},
            {"type": "join", "id": 1},
        ],
    }
    apply_floor_list_page(out_e2, limit=1, cursor="mail:9", partset={"events"})
    assert out_e2["events"][0]["type"] == "todo" and out_e2["next"] == "todo:9"

    out_w = {
        "mailbox": [],
        "needs": [],
        "issues": [],
        "agents": [],
        "kpis": [],
        "locks": [],
        "watchers": [{"type": "mail", "id": i} for i in (3, 2, 1)],
        "events": [],
    }
    apply_floor_list_page(out_w, limit=2, cursor=None, partset={"watchers"})
    assert len(out_w["watchers"]) == 2 and out_w["next"] == "mail:2"


def test_apply_floor_trees_untouched() -> None:
    trees = [{"name": "TREE_x", "nodes": [{"id": 1}, {"id": 2}, {"id": 3}]}]
    out = {
        "mailbox": [{"id": i} for i in range(10, 0, -1)],
        "needs": [],
        "issues": [],
        "agents": [],
        "kpis": [],
        "locks": [],
        "watchers": [],
        "events": [],
        "trees": trees,
    }
    apply_floor_list_page(out, limit=2, cursor=None, partset={"mail", "trees"})
    assert out["trees"] is trees
    assert len(out["trees"][0]["nodes"]) == 3
    assert len(out["mailbox"]) == 2


def test_page_activity_rows() -> None:
    rows = [
        {"updated": f"t{i}", "type": "mail", "desk_id": i, "owner": "a", "n": 1}
        for i in range(1, 6)
    ]
    page, nxt = page_activity_rows(rows, limit=2, cursor=None)
    assert len(page) == 2 and page[0]["id"] and nxt
    page2, nxt2 = page_activity_rows(rows, limit=2, cursor=nxt)
    assert len(page2) == 2 and page2[0]["id"] != page[0]["id"]
    page3, nxt3 = page_activity_rows(rows, limit=2, cursor=nxt2)
    assert len(page3) == 1 and nxt3 is None




def test_events_page_after_board_view_ttl() -> None:
    """Paging before board_view TTL can yield next with events=[]. Fix: page after."""
    from datetime import datetime, timedelta

    now = datetime(2026, 9, 26, 16, 0, 0)
    aged = (now - timedelta(hours=2)).isoformat(sep=" ")
    # >limit aged events => pre-filter page would set next; TTL drops all
    events = [
        {"type": "todo", "id": i, "at": aged, "project_id": "PROJ_demo"}
        for i in range(1, 60)
    ]
    base = {
        "mailbox": [],
        "needs": [],
        "issues": [],
        "agents": [],
        "kpis": [],
        "locks": [],
        "watchers": [],
        "events": events,
        "spend": [],
        "spend_lines": [],
        "projects": ["PROJ_demo"],
        "version": "0.5.6",
    }
    # Bug order: page then TTL => next set, events empty
    buggy = {**base, "events": [dict(e) for e in events]}
    apply_floor_list_page(buggy, limit=50, cursor=None, partset={"events"})
    assert buggy["next"] is not None
    buggy_view = board_view(buggy, now=now, decay=15 * 60)
    assert buggy_view["events"] == []
    assert buggy_view.get("next") == buggy["next"]  # stale next survives

    # Fixed order: TTL then page => next null when nothing survives
    fixed = {**base, "events": [dict(e) for e in events]}
    viewed = board_view(fixed, now=now, decay=15 * 60)
    apply_floor_list_page(viewed, limit=50, cursor=None, partset={"events"})
    assert viewed["events"] == []
    assert viewed["next"] is None

    # Fresh events still page with next after TTL
    fresh_at = now.isoformat(sep=" ")
    mixed = {
        **base,
        "events": [
            {"type": "todo", "id": i, "at": fresh_at, "project_id": "PROJ_demo"}
            for i in range(1, 6)
        ],
    }
    viewed2 = board_view(mixed, now=now, decay=15 * 60)
    apply_floor_list_page(viewed2, limit=2, cursor=None, partset={"events"})
    assert len(viewed2["events"]) == 2
    assert viewed2["next"] == "todo:2"


def test_floor_and_activity_routes_pass_limit_cursor(monkeypatch) -> None:
    monkeypatch.setattr("agent_coord.server.admin.door.mode", lambda: "path")
    monkeypatch.setattr("agent_coord.server.allow.allowed", lambda *a, **k: True)

    class _C:
        _cn = object()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr("agent_coord.server.middleware._office", lambda: _C())
    seen: dict[str, dict] = {}

    def _agents(cn, *a, **k):
        seen["agents"] = k
        return {
            "at": "t",
            "node": "n",
            "version": "0.5.6",
            "parts": ["agents"],
            "agents": [{"id": 1, "owner": "a"}],
            "next": None,
            "fp": {"agents": "a" * 16},
        }

    def _timeline(cn, project, window="24h"):
        return [{"updated": "t", "type": "mail", "desk_id": 1, "owner": "a", "n": 1, "id": "x"}]

    monkeypatch.setattr("agent_coord.server.records.floor.v1_agents", _agents)
    monkeypatch.setattr("agent_coord.server.records.floor._timeline", _timeline)
    root = Path(__file__).resolve().parents[2]
    client = TestClient(make_asgi_app(parse_roots(cwd=root), api_only=True))
    # clear floor cache between shapes
    import agent_coord.server.middleware as mw

    mw._floor_cache.clear()
    mw._floor_flight.clear()
    r = client.get("/api/v1/agents?project=demo&limit=3&cursor=9")
    assert r.status_code == 200
    assert seen["agents"]["limit"] == 3
    assert seen["agents"]["cursor"] == "9"
    assert "next" in r.json()
    r2 = client.get("/api/activity?project=demo&limit=1")
    assert r2.status_code == 200
    body = r2.json()
    assert "next" in body
    assert len(body["rows"]) <= 1
