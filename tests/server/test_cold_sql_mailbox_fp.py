# -*- coding: utf-8 -*-
"""Unit tests: mailbox JOIN collapse + v1 empty-on-match fp (no MySQL required)."""
from __future__ import annotations

from agent_coord.server.records.mail import group_list_rows
from agent_coord.server.records.floor import v1_agents, v1_events, v1_holds, v1_mailbox, v1_names, v1_scores, v1_todos, v1_watchers


def test_group_list_rows_collapses_dests() -> None:
    rows = [
        {
            "id": 10,
            "created": "2026-01-01 00:00:00",
            "desk": "DESK_a",
            "sender_roster": "ROLE_Builder",
            "body": "hi",
            "dst": "DESK_b",
            "roster": "PROJ_demo",
            "receipt": 0,
            "dst_id": 2,
        },
        {
            "id": 10,
            "created": "2026-01-01 00:00:00",
            "desk": "DESK_a",
            "sender_roster": "ROLE_Builder",
            "body": "hi",
            "dst": "DESK_c",
            "roster": None,
            "receipt": 1,
            "dst_id": 3,
        },
        {
            "id": 11,
            "created": "2026-01-02 00:00:00",
            "desk": "DESK_b",
            "sender_roster": None,
            "body": "yo",
            "dst": "DESK_a",
            "roster": None,
            "receipt": 0,
            "dst_id": 1,
        },
    ]
    grouped = group_list_rows(rows)
    assert len(grouped) == 2
    letter10, dests10 = grouped[0]
    assert letter10["id"] == 10
    assert letter10["body"] == "hi"
    assert [d["desk"] for d in dests10] == ["DESK_b", "DESK_c"]
    letter11, dests11 = grouped[1]
    assert letter11["id"] == 11
    assert len(dests11) == 1


def test_v1_mailbox_empty_on_match(monkeypatch) -> None:
    monkeypatch.setattr(
        "agent_coord.server.records.floor._projects_part_fp",
        lambda cn, ps, part: "aaaaaaaaaaaaaaaa",
    )
    called = {"n": 0}

    def boom(*a, **k):
        called["n"] += 1
        raise AssertionError("build_mailbox must not run on fp hit")

    monkeypatch.setattr("agent_coord.server.records.floor.build_mailbox", boom)
    hit = v1_mailbox(
        object(),
        projects=["demo"],
        client_fps={"mail": "aaaaaaaaaaaaaaaa"},
    )
    assert hit["mailbox"] == []
    assert hit["desk_unread"] == {}
    assert hit["fp"]["mail"] == "aaaaaaaaaaaaaaaa"
    assert called["n"] == 0

    monkeypatch.setattr(
        "agent_coord.server.records.floor.build_mailbox",
        lambda *a, **k: ([{"id": 1}], {"x": 1}),
    )
    miss = v1_mailbox(object(), projects=["demo"], client_fps={"mail": "bbbbbbbbbbbbbbbb"})
    assert miss["mailbox"] == [{"id": 1}]
    assert miss["desk_unread"] == {"x": 1}


def test_v1_todos_empty_on_match(monkeypatch) -> None:
    monkeypatch.setattr(
        "agent_coord.server.records.floor._projects_part_fp",
        lambda cn, ps, part: "cccccccccccccccc",
    )

    def boom(*a, **k):
        raise AssertionError("build_todos must not run on fp hit")

    monkeypatch.setattr("agent_coord.server.records.floor.build_todos", boom)
    hit = v1_todos(
        object(),
        projects=["demo"],
        client_fps={"todos": "cccccccccccccccc"},
    )
    assert hit["needs"] == []
    assert hit["issues"] == []
    assert hit["fp"]["todos"] == "cccccccccccccccc"


def test_v1_agents_empty_on_match(monkeypatch) -> None:
    monkeypatch.setattr(
        "agent_coord.server.records.floor._projects_part_fp",
        lambda cn, ps, part: "dddddddddddddddd",
    )

    def boom(*a, **k):
        raise AssertionError("build_agents must not run on fp hit")

    monkeypatch.setattr("agent_coord.server.records.floor.build_agents", boom)
    hit = v1_agents(
        object(),
        projects=["demo"],
        client_fps={"agents": "dddddddddddddddd"},
    )
    assert hit["agents"] == []
    assert hit["next"] is None
    assert hit["fp"]["agents"] == "dddddddddddddddd"

    monkeypatch.setattr(
        "agent_coord.server.records.floor.build_agents",
        lambda *a, **k: [{"id": "a1", "owner": "a1"}],
    )
    miss = v1_agents(object(), projects=["demo"], client_fps={"agents": "eeeeeeeeeeeeeeee"})
    assert miss["agents"] == [{"id": "a1", "owner": "a1"}]
    assert miss["next"] is None


def test_v1_scores_empty_on_match(monkeypatch) -> None:
    monkeypatch.setattr(
        "agent_coord.server.records.floor._projects_part_fp",
        lambda cn, ps, part: "ffffffffffffffff",
    )

    def boom(*a, **k):
        raise AssertionError("build_scores must not run on fp hit")

    monkeypatch.setattr("agent_coord.server.records.floor.build_scores", boom)
    hit = v1_scores(
        object(),
        projects=["demo"],
        client_fps={"scores": "ffffffffffffffff"},
    )
    assert hit["kpis"] == []
    assert hit["next"] is None
    assert hit["fp"]["scores"] == "ffffffffffffffff"

    monkeypatch.setattr(
        "agent_coord.server.records.floor.build_scores",
        lambda *a, **k: [{"id": "o|k|a", "owner": "o", "kpi": "k"}],
    )
    miss = v1_scores(object(), projects=["demo"], client_fps={"scores": "0000000000000000"})
    assert miss["kpis"] == [{"id": "o|k|a", "owner": "o", "kpi": "k"}]
    assert miss["next"] is None


def test_v1_holds_empty_on_match(monkeypatch) -> None:
    monkeypatch.setattr(
        "agent_coord.server.records.floor._projects_part_fp",
        lambda cn, ps, part: "1122334455667788",
    )

    def boom(*a, **k):
        raise AssertionError("build_holds must not run on fp hit")

    monkeypatch.setattr("agent_coord.server.records.floor.build_holds", boom)
    hit = v1_holds(
        object(),
        projects=["demo"],
        client_fps={"holds": "1122334455667788"},
    )
    assert hit["locks"] == []
    assert hit["next"] is None
    assert hit["fp"]["holds"] == "1122334455667788"

    monkeypatch.setattr(
        "agent_coord.server.records.floor.build_holds",
        lambda *a, **k: [{"id": "res|own|aff", "resource": "res", "owner": "own"}],
    )
    miss = v1_holds(object(), projects=["demo"], client_fps={"holds": "0000000000000000"})
    assert miss["locks"] == [{"id": "res|own|aff", "resource": "res", "owner": "own"}]
    assert miss["next"] is None


def test_v1_watchers_empty_on_match(monkeypatch) -> None:
    monkeypatch.setattr(
        "agent_coord.server.records.floor._projects_part_fp",
        lambda cn, ps, part: "aabbccddeeff0011",
    )

    def boom(*a, **k):
        raise AssertionError("build_watchers must not run on fp hit")

    monkeypatch.setattr("agent_coord.server.records.floor.build_watchers", boom)
    hit = v1_watchers(
        object(),
        projects=["demo"],
        client_fps={"watchers": "aabbccddeeff0011"},
    )
    assert hit["watchers"] == []
    assert hit["next"] is None
    assert hit["fp"]["watchers"] == "aabbccddeeff0011"

    monkeypatch.setattr(
        "agent_coord.server.records.floor.build_watchers",
        lambda *a, **k: [{"type": "todo", "id": 3, "title": "t"}],
    )
    miss = v1_watchers(object(), projects=["demo"], client_fps={"watchers": "0000000000000000"})
    assert miss["watchers"] == [{"type": "todo", "id": 3, "title": "t"}]
    assert miss["next"] is None



def test_v1_events_empty_on_match(monkeypatch) -> None:
    monkeypatch.setattr(
        "agent_coord.server.records.floor._projects_part_fp",
        lambda cn, ps, part: "aabbccddeeff0011",
    )

    def boom(*a, **k):
        raise AssertionError("build_events must not run on fp hit")

    monkeypatch.setattr("agent_coord.server.records.floor.build_events", boom)
    hit = v1_events(
        object(),
        projects=["demo"],
        client_fps={"events": "aabbccddeeff0011"},
    )
    assert hit["events"] == []
    assert hit["next"] is None
    assert hit["fp"]["events"] == "aabbccddeeff0011"

    monkeypatch.setattr(
        "agent_coord.server.records.floor.build_events",
        lambda *a, **k: [{"type": "todo", "id": 7, "kind": "todo"}],
    )
    miss = v1_events(object(), projects=["demo"], client_fps={"events": "0000000000000000"})
    assert miss["events"] == [{"type": "todo", "id": 7, "kind": "todo"}]
    assert miss["next"] is None



def test_v1_names_empty_on_match(monkeypatch) -> None:
    monkeypatch.setattr(
        "agent_coord.server.records.floor._projects_part_fp",
        lambda cn, ps, part: "bbccddeeff001122",
    )

    def boom(*a, **k):
        raise AssertionError("build_names must not run on fp hit")

    monkeypatch.setattr("agent_coord.server.records.floor.build_names", boom)
    hit = v1_names(
        object(),
        projects=["demo"],
        client_fps={"names": "bbccddeeff001122"},
    )
    assert hit["catalog"] == []
    assert hit["next"] is None
    assert hit["fp"]["names"] == "bbccddeeff001122"

    monkeypatch.setattr(
        "agent_coord.server.records.floor.build_names",
        lambda *a, **k: [{"kind": "project", "name": "demo", "deleted": False}],
    )
    miss = v1_names(object(), projects=["demo"], client_fps={"names": "0000000000000000"})
    assert miss["catalog"] == [{"kind": "project", "name": "demo", "deleted": False}]
    assert miss["next"] is None


def test_group_list_rows_reads_dests_json() -> None:
    import json

    rows = [
        {
            "id": 12,
            "created": "2026-01-03 00:00:00",
            "desk": "DESK_a",
            "sender_roster": None,
            "body": "agg",
            "dests": json.dumps(
                [
                    {"desk_id": 3, "desk": "DESK_c", "desk_type": "desk", "receipt": 1},
                    {"desk_id": 2, "desk": "DESK_b", "desk_type": "desk", "receipt": 0},
                ]
            ),
        }
    ]
    grouped = group_list_rows(rows)
    assert len(grouped) == 1
    letter, dests = grouped[0]
    assert letter["id"] == 12
    assert [d["desk"] for d in dests] == ["DESK_b", "DESK_c"]
    assert dests[1]["receipt"] == 1 and dests[1]["roster"] is None
