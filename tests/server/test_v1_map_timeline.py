# -*- coding: utf-8 -*-
"""GET /api/v1/map and /api/v1/timeline joined FLOOR hybrid isolates."""
from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from agent_coord.lib.observe import parse_roots
from agent_coord.server.asgi import make_asgi_app


def _client(monkeypatch) -> TestClient:
    monkeypatch.setattr("agent_coord.server.admin.door.mode", lambda: "path")
    monkeypatch.setattr("agent_coord.server.allow.allowed", lambda *a, **k: True)
    root = Path(__file__).resolve().parents[2]
    app = make_asgi_app(parse_roots(cwd=root), api_only=True)
    return TestClient(app)


class _C:
    _cn = object()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_v1_map_timeline_require_project(monkeypatch) -> None:
    client = _client(monkeypatch)
    for path in ("/api/v1/map", "/api/v1/timeline"):
        r = client.get(path)
        assert r.status_code == 400, path
        body = r.json()
        assert "project" in body["error"]
        assert "mill" in body


def test_v1_map_joined_agents_mail(monkeypatch) -> None:
    monkeypatch.setattr(
        "agent_coord.server.records.floor.v1_map",
        lambda cn, **k: {
            "at": "t",
            "node": "n",
            "version": "0.5.8",
            "parts": ["agents", "mail"],
            "agents": [{"id": "desk_a", "owner": "desk_a"}],
            "mailbox": [{"id": 1}],
            "desk_unread": {"desk_a": 1},
            "next": None,
            "fp": {"agents": "1122334455667788", "mail": "0123456789abcdef"},
        },
    )
    monkeypatch.setattr("agent_coord.server.middleware._office", lambda: _C())
    client = _client(monkeypatch)
    r = client.get("/api/v1/map?project=demo")
    assert r.status_code == 200
    body = r.json()
    assert body["mill"]
    assert body["parts"] == ["agents", "mail"]
    assert body["agents"][0]["owner"] == "desk_a"
    assert body["mailbox"][0]["id"] == 1
    assert body["desk_unread"]["desk_a"] == 1
    assert body["fp"]["mail"] == "0123456789abcdef"
    assert "timings" not in body

    timed = client.get("/api/v1/map?project=demo&timings=1")
    assert timed.status_code == 200
    tb = timed.json()
    assert "timings" in tb
    assert tb["timings"]["n"] == 1
    assert "sql_ms" in tb["timings"]
    assert "resp_b" in tb["timings"]


def test_v1_timeline_default_agents_events(monkeypatch) -> None:
    seen = {}

    def _fake(cn, **k):
        seen["parts"] = k.get("parts")
        seen["limit"] = k.get("limit")
        seen["cursor"] = k.get("cursor")
        return {
            "at": "t",
            "node": "n",
            "version": "0.5.8",
            "parts": ["agents", "events"],
            "agents": [{"id": "desk_a", "owner": "desk_a"}],
            "events": [{"type": "todo", "id": 7, "kind": "todo"}],
            "next": None,
            "fp": {"agents": "1122334455667788", "events": "aabbccddeeff0011"},
        }

    monkeypatch.setattr("agent_coord.server.records.floor.v1_timeline", _fake)
    monkeypatch.setattr("agent_coord.server.middleware._office", lambda: _C())
    client = _client(monkeypatch)
    r = client.get("/api/v1/timeline?project=demo&limit=9&cursor=todo:3")
    assert r.status_code == 200
    body = r.json()
    assert body["parts"] == ["agents", "events"]
    assert body["agents"][0]["id"] == "desk_a"
    assert body["events"][0]["id"] == 7
    assert body["fp"]["events"] == "aabbccddeeff0011"
    assert seen["parts"] is None  # default LAN style; builder chooses events
    assert seen["limit"] == 9
    assert seen["cursor"] == "todo:3"


def test_v1_timeline_parts_agents_timeline(monkeypatch) -> None:
    seen = {}

    def _fake(cn, **k):
        seen["parts"] = k.get("parts")
        return {
            "at": "t",
            "node": "n",
            "version": "0.5.8",
            "parts": ["agents", "timeline"],
            "agents": [{"id": "desk_b", "owner": "desk_b"}],
            "timeline": [{"id": "u|todo|1|o|a", "type": "todo", "n": 2}],
            "next": None,
            "fp": {"agents": "9988776655443322"},
        }

    monkeypatch.setattr("agent_coord.server.records.floor.v1_timeline", _fake)
    monkeypatch.setattr("agent_coord.server.middleware._office", lambda: _C())
    client = _client(monkeypatch)
    r = client.get("/api/v1/timeline?project=demo&parts=agents,timeline&timings=1")
    assert r.status_code == 200
    body = r.json()
    assert body["parts"] == ["agents", "timeline"]
    assert body["timeline"][0]["type"] == "todo"
    assert "events" not in body or body.get("events") in (None, [])
    assert body["timings"]["n"] == 1
    assert seen["parts"] == ["agents", "timeline"]


def test_v1_map_builder_fp_skip_and_keys(monkeypatch) -> None:
    """Unit: builder reuses floor part builders; fp skip empties lists."""
    from agent_coord.server.records import floor as rec_floor

    calls = {"agents": 0, "mailbox": 0}

    def fake_agents(cn, mail_ps, want):
        calls["agents"] += 1
        return [{"owner": "desk_a", "pid": ""}]

    def fake_mailbox(cn, mail_ps, want):
        calls["mailbox"] += 1
        return [{"id": 42}], {"desk_a": 1}

    monkeypatch.setattr(rec_floor, "build_agents", fake_agents)
    monkeypatch.setattr(rec_floor, "build_mailbox", fake_mailbox)
    monkeypatch.setattr(
        rec_floor,
        "_projects_part_fp",
        lambda cn, ps, part: {"agents": "aaaabbbbccccdddd", "mail": "1111222233334444"}[part],
    )

    cold = rec_floor.v1_map(object(), projects=["demo"])
    assert cold["parts"] == ["agents", "mail"]
    assert cold["agents"][0]["id"] == "desk_a"
    assert cold["mailbox"][0]["id"] == 42
    assert cold["desk_unread"]["desk_a"] == 1
    assert cold["fp"]["agents"] == "aaaabbbbccccdddd"
    assert calls == {"agents": 1, "mailbox": 1}

    skipped = rec_floor.v1_map(
        object(),
        projects=["demo"],
        client_fps={"agents": "aaaabbbbccccdddd", "mail": "1111222233334444"},
    )
    assert skipped["agents"] == []
    assert skipped["mailbox"] == []
    assert skipped["desk_unread"] == {}
    assert skipped["fp"]["mail"] == "1111222233334444"
    assert calls == {"agents": 1, "mailbox": 1}  # no rebuild on full fp match


def test_v1_timeline_builder_events_and_timeline_variants(monkeypatch) -> None:
    from agent_coord.server.records import floor as rec_floor

    monkeypatch.setattr(
        rec_floor,
        "build_agents",
        lambda cn, mail_ps, want: [{"owner": "desk_a"}],
    )
    monkeypatch.setattr(
        rec_floor,
        "build_events",
        lambda cn, mail_ps, want: [{"type": "todo", "id": 9, "kind": "todo"}],
    )
    monkeypatch.setattr(
        rec_floor,
        "_timeline",
        lambda cn, project, window="24h": [
            {"updated": "t", "type": "todo", "desk_id": 1, "owner": "desk_a", "roster_id": "demo", "n": 3}
        ],
    )
    monkeypatch.setattr(rec_floor, "_projects_part_fp", lambda cn, ps, part: "abcdabcdabcdabcd")

    lan = rec_floor.v1_timeline(object(), projects=["demo"])
    assert lan["parts"] == ["agents", "events"]
    assert lan["events"][0]["id"] == 9
    assert "timeline" not in lan

    proj = rec_floor.v1_timeline(object(), projects=["demo"], parts=["agents", "timeline"])
    assert proj["parts"] == ["agents", "timeline"]
    assert proj["timeline"][0]["type"] == "todo"
    assert proj["timeline"][0]["id"]  # stamped
    assert "events" not in proj
