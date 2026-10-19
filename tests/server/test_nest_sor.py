# -*- coding: utf-8 -*-
"""A3 Nest SoR: stamp formula + score_tick scrape."""
from datetime import datetime, timezone
from pathlib import Path

from agent_coord.server import nest_sor as ns
from agent_coord.server.score_tick import (
    BOOK_PERF,
    BOOK_TARGET,
    KPI_NEST_HIT,
    KPI_NEST_REASK,
    measure,
    measure_nest_sor,
)


def setup_function() -> None:
    ns.reset_for_tests()


def test_book_nest_kpi_formula() -> None:
    assert KPI_NEST_HIT in BOOK_PERF
    assert KPI_NEST_REASK in BOOK_PERF
    assert BOOK_TARGET[KPI_NEST_HIT] == ""
    assert BOOK_TARGET[KPI_NEST_REASK] == ""
    assert KPI_NEST_HIT == "mill-office.nest_hit_n"
    assert KPI_NEST_REASK == "mill-office.nest_reask_n"
    assert "nest" in BOOK_PERF[KPI_NEST_HIT].lower()
    assert "re-ask" in BOOK_PERF[KPI_NEST_REASK].lower() or "reask" in BOOK_PERF[KPI_NEST_REASK].lower()


def test_first_hit_then_reask(monkeypatch) -> None:
    lines: list[str] = []

    def fake_perf(op: str, ms: float, **kv):
        parts = [f"op={op}", f"ms={ms:.1f}"] + [f"{k}={v}" for k, v in kv.items()]
        lines.append(" ".join(parts))

    monkeypatch.setattr("agent_coord.server.push.perf_log", fake_perf)
    desk = "DESK_builder"
    card = {"id": 56, "need_id": "agent-value-kpi-a1-a6", "nest": 1, "status": "open"}
    body = {"need": "agent-value-kpi-a1-a6"}
    ns.note_nest(desk, "todo", [card], body=body)
    assert len(lines) == 1
    assert "op=nest.hit" in lines[0]
    assert "todo=56" in lines[0]
    assert "reask=0" in lines[0]
    assert "desk=DESK_builder" in lines[0]
    assert ns.seen_snapshot(desk, 56) == 1
    ns.note_nest(desk, "todo", [card], body=body)
    assert len(lines) == 2
    assert "reask=1" in lines[1]
    assert ns.seen_snapshot(desk, 56) == 2


def test_non_nest_no_stamp(monkeypatch) -> None:
    lines: list[tuple] = []
    monkeypatch.setattr(
        "agent_coord.server.push.perf_log",
        lambda op, ms, **kv: lines.append((op, ms, kv)),
    )
    ns.note_nest(
        "DESK_a",
        "todo",
        [{"id": 1, "need_id": "x", "nest": 0}],
        body={"need": "x"},
    )
    ns.note_nest(
        "DESK_a",
        "todo",
        [{"id": 2, "need_id": "y"}],
        body={"need": "y"},
    )
    assert lines == []


def test_board_list_without_need_skipped(monkeypatch) -> None:
    lines: list[tuple] = []
    monkeypatch.setattr(
        "agent_coord.server.push.perf_log",
        lambda op, ms, **kv: lines.append((op, ms, kv)),
    )
    ns.note_nest(
        "DESK_a",
        "todo",
        [{"id": 56, "need_id": "agent-value-kpi-a1-a6", "nest": 1}],
        body={},  # no need => board list
    )
    assert lines == []


def test_multi_card_result_skipped(monkeypatch) -> None:
    lines: list[tuple] = []
    monkeypatch.setattr(
        "agent_coord.server.push.perf_log",
        lambda op, ms, **kv: lines.append((op, ms, kv)),
    )
    ns.note_nest(
        "DESK_a",
        "todo",
        [
            {"id": 1, "need_id": "a", "nest": 1},
            {"id": 2, "need_id": "b", "nest": 1},
        ],
        body={"need": "a"},
    )
    assert lines == []


def test_measure_nest_sor_counts() -> None:
    text = "\n".join(
        [
            "2026-09-27T10:00:00Z op=nest.hit ms=0.0 todo=56 need=a desk=DESK_a reask=0 ok=1",
            "2026-09-27T10:00:01Z op=nest.hit ms=0.0 todo=56 need=a desk=DESK_a reask=1 ok=1",
            "2026-09-27T10:00:02Z op=nest.hit ms=0.0 todo=57 need=b desk=DESK_b reask=0 ok=1",
            "2026-09-27T09:00:00Z op=nest.hit ms=0.0 todo=9 need=old desk=DESK_old reask=1 ok=1",
        ]
    )
    since = datetime(2026, 9, 27, 9, 30, 0, tzinfo=timezone.utc)
    assert measure_nest_sor(text, since) == (3, 1)


def test_measure_includes_nest_kpis(tmp_path: Path) -> None:
    (tmp_path / "mill-perf.log").write_text(
        "2026-09-27T10:00:00Z op=nest.hit ms=0.0 todo=56 need=x desk=DESK_x reask=1 ok=1\n",
        encoding="utf-8",
    )
    now = datetime(2026, 9, 27, 10, 30, 0, tzinfo=timezone.utc)
    row = measure(dest=tmp_path, window_s=3600, now=now)
    assert row[KPI_NEST_HIT] == 1
    assert row[KPI_NEST_REASK] == 1


def test_publish_book_perf_nest_empty_target() -> None:
    from agent_coord.server import score_tick as st

    for kpi in (KPI_NEST_HIT, KPI_NEST_REASK):
        tgt = st.BOOK_TARGET.get(kpi, st.TARGET)
        assert tgt == ""
