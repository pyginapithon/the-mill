"""F38 (score-trend-met, #307) and the 0.7.6 score verb forms, no SQL.

Gardener's live series: three zeros read improving, and 14 then 16 with better
down read improving. The newest step now decides; equal values are never
improving; met replaces flat or improving at or past the target.
"""
from __future__ import annotations

import pytest

from agent_coord.helpers.errors import CoordError
from agent_coord.server import score_series as ss


@pytest.mark.parametrize(
    "vals,better,target,want",
    [
        # Gardener mail 1939
        ([0, 0, 0], "down", None, "flat"),
        ([0, 0, 0], "down", "0", "met"),
        ([0, 0, 0, 10], "down", None, "flat"),  # the live cold.retries series
        ([0, 0, 0, 2, 3, 4], "down", None, "flat"),
        ([16, 14, 19, 46], "down", None, "worse"),  # the live cold.commands series
        ([16, 14, 20, 22, 24, 26], "down", None, "worse"),  # small step back, old window better
        ([16, 14], "down", "10", "worse"),
        # a step back inside 2% is flat, never improving
        ([99, 100, 80, 80, 80, 80], "up", None, "flat"),
        ([101, 100, 120, 120], "down", None, "flat"),
        # equal values are flat whatever came before the window
        ([7, 7, 7, 7, 7, 7], "up", None, "flat"),
        ([7, 7, 7, 7, 7, 7], "down", None, "flat"),
        ([7, 7, 7, 7, 7, 7], "up", "5", "met"),
        # the newest step past 2% decides
        ([12, 10, 30, 30, 30, 30], "up", None, "improving"),
        ([8, 10, 1, 1, 1, 1], "up", None, "worse"),
        # met: at or past target, unless the step back is real
        ([500, 520], "down", "500", "met"),
        ([480, 470], "down", "500", "worse"),
        ([480, 481], "down", "500", "met"),
        ([51, 40], "up", "50", "met"),
        ([40, 30], "up", "50", "improving"),
        ([5], "up", "1", "new"),
        ([], "up", "1", "new"),
        ([3, 3], "up", "", "flat"),
        ([3, 3, 2], "up", None, "flat"),
        # a slow steady gain: each step under 2%, 3 back over 2%
        ([790, 800, 810, 820], "down", None, "improving"),
        ([102, 101, 100, 100], "up", None, "flat"),
    ],
)
def test_trend_newest_step_and_met(vals, better, target, want) -> None:
    assert ss.trend(vals, better, target) == want


@pytest.mark.parametrize(
    "raw,ok",
    [("90m", True), ("2h", True), ("3d", True), ("2026-10-18", True), ("2026-10-18T14:05", True),
     ("2026-10-18 14:05:09", True), ("2026-13-40", False), ("2026-02-30", False), ("5w", False),
     ("tomorrow", False), ("", False), ("1d; DROP", False), ("1234567d", False), ("2026-10-18T25:00", False)],
)
def test_at_shape(raw, ok) -> None:
    assert ss.at_ok(raw) is ok


class _Book:
    _cn = None


@pytest.fixture
def rec(monkeypatch):
    from agent_coord.server.api.mill import rpc
    from agent_coord.server.records import score as rec_score

    calls: list[tuple] = []
    monkeypatch.setattr(rec_score, "point_add", lambda *a, **k: calls.append(("add", a[1:], k)) or [{"id": 7}])
    monkeypatch.setattr(rec_score, "define", lambda *a, **k: calls.append(("define", a[1:], k)) or [{"id": 7}])
    monkeypatch.setattr(rec_score, "retire", lambda *a, **k: calls.append(("retire", a[1:], k)) or [{"id": 7}])
    monkeypatch.setattr(rec_score, "points", lambda *a, **k: [])
    monkeypatch.setattr(rpc, "_poke", lambda *a, **k: None)
    import agent_coord.server.admin.guard as guard

    monkeypatch.setattr(guard, "is_role_admin", lambda cn, desk: desk == "boss")
    return rpc, calls


def test_target_alone_defines_without_a_point(rec) -> None:
    rpc, calls = rec
    rpc._h_score(_Book(), {"name": "k", "target": "5", "better": "down"}, "r", "d1")
    assert calls == [("define", ("r", "d1", "k"), {"target": "5", "better": "down", "unit": None})]


def test_unit_alone_defines(rec) -> None:
    rpc, calls = rec
    rpc._h_score(_Book(), {"name": "k", "unit": "ms"}, "r", "d1")
    assert calls[0][0] == "define" and calls[0][2]["unit"] == "ms"


def test_name_alone_is_still_a_read(rec) -> None:
    rpc, calls = rec
    with pytest.raises(CoordError, match="no score k on r"):
        rpc._h_score(_Book(), {"name": "k"}, "r", "d1")
    assert calls == []


def test_at_rides_the_point(rec) -> None:
    rpc, calls = rec
    rpc._h_score(_Book(), {"name": "k", "value": "3", "at": "2h"}, "r", "d1")
    assert calls[0][0] == "add" and calls[0][2]["at"] == "2h"


@pytest.mark.parametrize(
    "body,msg",
    [
        ({"name": "k", "at": "2h"}, "--at needs a VALUE"),
        ({"name": "k", "value": "1", "at": "soon"}, "--at must be"),
        ({"name": "k", "target": "x"}, "--target must be a number"),
        ({"name": "k", "target": "1", "note": "n"}, "--note goes with a VALUE"),
        ({"retire": True}, "retire needs ROSTER NAME"),
        ({"name": "k", "retire": True, "at": "1d"}, "retire takes no VALUE or --at"),
    ],
)
def test_refusals_store_nothing(rec, body, msg) -> None:
    rpc, calls = rec
    with pytest.raises(CoordError, match=msg):
        rpc._h_score(_Book(), body, "r", "d1")
    assert calls == []


def test_retire_passes_admin_flag(rec) -> None:
    rpc, calls = rec
    assert rpc._h_score(_Book(), {"name": "k", "retire": True}, "r", "boss")["retired"] is True
    rpc._h_score(_Book(), {"name": "k", "retire": True}, "r", "d1")
    assert [c[2]["admin"] for c in calls] == [True, False]


def test_cli_retire_score_rides_the_score_verb(monkeypatch) -> None:
    from agent_coord.__main__ import _build_parser
    from agent_coord.client import language
    from agent_coord.client import outbound

    monkeypatch.setattr("agent_coord.client.tokens.resolve_desk_owner", lambda _x: "d1")
    args = _build_parser().parse_args(["retire", "score", "cold-test", "gardener-go-probe", "--yes"])
    args = language.translate(args)
    body = outbound.body_from_args(args)
    assert body["verb"] == "score" and body["project"] == "cold-test"
    assert body["name"] == "gardener-go-probe" and body["retire"] is True


def test_cli_retire_score_needs_a_name_and_names_take_one() -> None:
    from agent_coord.__main__ import _build_parser
    from agent_coord.client import language

    with pytest.raises(CoordError, match="mill retire score ROSTER NAME"):
        language.translate(_build_parser().parse_args(["retire", "score", "cold-test", "--yes"]))
    with pytest.raises(CoordError, match="takes one NAME"):
        language.translate(_build_parser().parse_args(["retire", "label", "bug", "extra", "--yes"]))


def test_cli_score_at_is_sent() -> None:
    from agent_coord.__main__ import _build_parser

    args = _build_parser().parse_args(["score", "r", "k", "3", "--at", "2h"])
    assert args.at == "2h"
