# -*- coding: utf-8 -*-
"""A5 hold-blocked: stamp formula + score_tick scrape."""
import time
from datetime import datetime, timezone
from pathlib import Path

from agent_coord.server import hold_blocked as hb
from agent_coord.server.score_tick import (
    BOOK_PERF,
    BOOK_TARGET,
    KPI_HOLD_BLOCKED_MS,
    measure,
    measure_hold_blocked,
)


def setup_function() -> None:
    hb.reset_for_tests()


def test_book_hold_blocked_kpi_formula() -> None:
    assert KPI_HOLD_BLOCKED_MS in BOOK_PERF
    assert BOOK_TARGET[KPI_HOLD_BLOCKED_MS] == ""
    assert "hold" in BOOK_PERF[KPI_HOLD_BLOCKED_MS].lower()
    assert "sum" in BOOK_PERF[KPI_HOLD_BLOCKED_MS].lower()
    assert KPI_HOLD_BLOCKED_MS == "mill-office.hold_blocked_ms"


def test_deny_then_acquire_stamps_once(monkeypatch) -> None:
    lines: list[str] = []

    def fake_perf(op: str, ms: float, **kv):
        parts = [f"op={op}", f"ms={ms:.1f}"] + [f"{k}={v}" for k, v in kv.items()]
        lines.append(" ".join(parts))

    monkeypatch.setattr("agent_coord.server.push.perf_log", fake_perf)
    desk = "DESK_builder"
    res = "RES_tree_floor"
    # deny: start wait
    hb.note_hold(
        desk,
        "hold",
        {"ok": False, "resource": res, "owner": "DESK_scout", "id": 9},
        body={"resource": res},
    )
    snap = hb.wait_snapshot(desk, res)
    assert snap is not None and snap.get("stamped") is False
    assert snap.get("holder") == "DESK_scout"
    assert len(lines) == 0
    time.sleep(0.02)
    # acquire: stamp
    hb.note_hold(
        desk,
        "hold",
        {"ok": True, "resource": res, "owner": desk, "id": 9},
        body={"resource": res},
    )
    assert len(lines) == 1
    assert "op=hold.blocked" in lines[0]
    assert "desk=DESK_builder" in lines[0]
    assert "resource=" in lines[0]
    assert "holder=DESK_scout" in lines[0]
    assert "ok=1" in lines[0]
    assert hb.wait_snapshot(desk, res) is None
    # ms should be at least ~20
    assert "ms=" in lines[0]


def test_acquire_without_prior_deny_no_stamp(monkeypatch) -> None:
    lines: list[tuple] = []
    monkeypatch.setattr(
        "agent_coord.server.push.perf_log",
        lambda op, ms, **kv: lines.append((op, ms, kv)),
    )
    desk = "DESK_agent"
    res = "RES_doc"
    hb.note_hold(desk, "hold", {"ok": True, "resource": res, "id": 1}, body={"resource": res})
    assert lines == []
    assert hb.wait_snapshot(desk, res) is None


def test_repeated_deny_keeps_t0(monkeypatch) -> None:
    lines: list[tuple] = []
    monkeypatch.setattr(
        "agent_coord.server.push.perf_log",
        lambda op, ms, **kv: lines.append((op, ms, kv)),
    )
    desk = "DESK_a"
    res = "RES_x"
    hb.note_hold(desk, "hold", {"ok": False, "resource": res, "owner": "DESK_b"}, body={"resource": res})
    t0 = hb.wait_snapshot(desk, res)["t0"]
    time.sleep(0.01)
    hb.note_hold(desk, "hold", {"ok": False, "resource": res, "owner": "DESK_b"}, body={"resource": res})
    assert hb.wait_snapshot(desk, res)["t0"] == t0
    assert lines == []


def test_non_hold_command_ignored(monkeypatch) -> None:
    lines: list[tuple] = []
    monkeypatch.setattr(
        "agent_coord.server.push.perf_log",
        lambda op, ms, **kv: lines.append((op, ms, kv)),
    )
    hb.note_hold("DESK_a", "drop", {"ok": True, "resource": "RES_x"}, body={"resource": "RES_x"})
    hb.note_hold("DESK_a", "claim", {"ok": True, "need_id": "x"}, body={})
    assert lines == []


def test_measure_hold_blocked_sum() -> None:
    text = "\n".join(
        [
            "2026-09-27T10:00:00Z op=hold.blocked ms=100.0 desk=DESK_a resource=RES_a holder=DESK_b ok=1",
            "2026-09-27T10:00:01Z op=hold.blocked ms=250.5 desk=DESK_c resource=RES_c holder=DESK_d ok=1",
            "2026-09-27T10:00:02Z op=hold.blocked ms=50.0 desk=DESK_e resource=RES_e holder=DESK_f ok=1",
            "2026-09-27T09:00:00Z op=hold.blocked ms=9999.0 desk=DESK_old resource=RES_old holder=DESK_z ok=1",
        ]
    )
    since = datetime(2026, 9, 27, 9, 30, 0, tzinfo=timezone.utc)
    # in-window: 100 + 250.5 + 50 = 400.5 -> round 400 or 401
    assert measure_hold_blocked(text, since) == 400


def test_measure_includes_hold_blocked_kpi(tmp_path: Path) -> None:
    (tmp_path / "mill-perf.log").write_text(
        "2026-09-27T10:00:00Z op=hold.blocked ms=1234.0 desk=DESK_x resource=RES_y holder=DESK_z ok=1\n",
        encoding="utf-8",
    )
    now = datetime(2026, 9, 27, 10, 30, 0, tzinfo=timezone.utc)
    row = measure(dest=tmp_path, window_s=3600, now=now)
    assert row[KPI_HOLD_BLOCKED_MS] == 1234


def test_publish_book_perf_hold_blocked_empty_target() -> None:
    from agent_coord.server import score_tick as st

    note = st.BOOK_PERF[KPI_HOLD_BLOCKED_MS]
    tgt = st.BOOK_TARGET.get(KPI_HOLD_BLOCKED_MS, st.TARGET)
    row = {"kpi": KPI_HOLD_BLOCKED_MS, "value": "500", "target": tgt, "note": note}
    assert row["target"] == ""
    assert row["value"] == "500"
