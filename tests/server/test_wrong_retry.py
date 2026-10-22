# -*- coding: utf-8 -*-
"""A2 wrong-command / retry: stamp formula + score_tick scrape."""
from datetime import datetime, timezone
from pathlib import Path

from agent_coord.server import wake_first as wf
from agent_coord.server.score_tick import (
    BOOK_PERF,
    BOOK_TARGET,
    KPI_RETRY,
    KPI_WRONG_N,
    measure,
    measure_wrong_retry,
)


def setup_function() -> None:
    wf.reset_for_tests()


def test_book_wrong_retry_kpi_formula() -> None:
    assert KPI_WRONG_N in BOOK_PERF
    assert KPI_RETRY in BOOK_PERF
    assert BOOK_TARGET[KPI_WRONG_N] == ""
    assert BOOK_TARGET[KPI_RETRY] == ""
    assert "non-ok" in BOOK_PERF[KPI_WRONG_N].lower() or "wrong" in BOOK_PERF[KPI_WRONG_N].lower()
    assert "retry" in BOOK_PERF[KPI_RETRY].lower() or "same-command" in BOOK_PERF[KPI_RETRY].lower()
    assert KPI_WRONG_N == "mill-office.wrong_verb_n"
    assert KPI_RETRY == "mill-office.retry_before_ok"


def test_wrong_retry_stamp_fields(monkeypatch) -> None:
    lines: list[str] = []

    def fake_perf(op: str, ms: float, **kv):
        parts = [f"op={op}", f"ms={ms:.1f}"] + [f"{k}={v}" for k, v in kv.items()]
        lines.append(" ".join(parts))

    monkeypatch.setattr("agent_coord.server.push.perf_log", fake_perf)
    desk = "DESK_builder"
    wf.mark_wake(desk)
    wf.note_rpc(desk, "heartbeat", ok=True)  # skip
    wf.note_rpc(desk, "todo", ok=False)  # wrong +1 (different command)
    wf.note_rpc(desk, "claim", ok=False)  # wrong +1, retry for claim
    wf.note_rpc(desk, "claim", ok=False)  # wrong +1, retry for claim
    wf.note_rpc(desk, "claim", ok=True)  # first ok -> stamp
    assert len(lines) == 1
    assert "op=wake.first_ok" in lines[0]
    assert "wrong=3" in lines[0]
    assert "retry=2" in lines[0]
    assert "verb=claim" in lines[0]
    assert "rpc=4" in lines[0]
    snap = wf.session_snapshot(desk)
    assert snap and snap["stamped"] is True


def test_wrong_zero_when_first_ok_clean(monkeypatch) -> None:
    lines: list[tuple] = []
    monkeypatch.setattr(
        "agent_coord.server.push.perf_log",
        lambda op, ms, **kv: lines.append((op, ms, kv)),
    )
    desk = "DESK_agent"
    wf.mark_wake(desk)
    wf.note_rpc(desk, "inbox", ok=True)
    assert len(lines) == 1
    assert lines[0][2]["wrong"] == 0
    assert lines[0][2]["retry"] == 0
    assert lines[0][2]["verb"] == "inbox"


def test_retry_only_same_command(monkeypatch) -> None:
    """wrong counts all non-ok; retry only prior fails of the ok command."""
    lines: list[tuple] = []
    monkeypatch.setattr(
        "agent_coord.server.push.perf_log",
        lambda op, ms, **kv: lines.append((op, ms, kv)),
    )
    desk = "DESK_scout"
    wf.mark_wake(desk)
    wf.note_rpc(desk, "send", ok=False)
    wf.note_rpc(desk, "send", ok=False)
    wf.note_rpc(desk, "hold", ok=True)  # first day-one ok is hold
    assert lines[0][2]["wrong"] == 2
    assert lines[0][2]["retry"] == 0  # hold never failed
    assert lines[0][2]["verb"] == "hold"


def test_measure_wrong_retry_p50() -> None:
    text = "\n".join(
        [
            "2026-09-27T10:00:00Z op=wake.first_ok ms=100.0 rpc=2 wrong=0 retry=0 desk=DESK_a verb=claim ok=1",
            "2026-09-27T10:00:01Z op=wake.first_ok ms=300.0 rpc=4 wrong=4 retry=2 desk=DESK_b verb=inbox ok=1",
            "2026-09-27T10:00:02Z op=wake.first_ok ms=200.0 rpc=3 wrong=2 retry=1 desk=DESK_c verb=send ok=1",
            "2026-09-27T09:00:00Z op=wake.first_ok ms=999.0 rpc=9 wrong=9 retry=9 desk=DESK_old verb=hold ok=1",
        ]
    )
    since = datetime(2026, 9, 27, 9, 30, 0, tzinfo=timezone.utc)
    wrong, retry = measure_wrong_retry(text, since)
    # sorted wrong 0,2,4 -> p50 index round(0.5*2)=1 -> 2
    assert wrong == 2
    # sorted retry 0,1,2 -> 1
    assert retry == 1


def test_measure_includes_wrong_retry_kpis(tmp_path: Path) -> None:
    (tmp_path / "mill-perf.log").write_text(
        "2026-09-27T10:00:00Z op=wake.first_ok ms=150.0 rpc=5 wrong=3 retry=2 desk=DESK_x verb=todo ok=1\n",
        encoding="utf-8",
    )
    now = datetime(2026, 9, 27, 10, 30, 0, tzinfo=timezone.utc)
    row = measure(dest=tmp_path, window_s=3600, now=now)
    assert row[KPI_WRONG_N] == 3
    assert row[KPI_RETRY] == 2


def test_publish_book_perf_wrong_retry_empty_target() -> None:
    from agent_coord.server import score_tick as st

    book = {KPI_WRONG_N: 2, KPI_RETRY: 1}
    rows = []
    for kpi, n in book.items():
        note = st.BOOK_PERF[kpi]
        tgt = st.BOOK_TARGET.get(kpi, st.TARGET)
        rows.append({"kpi": kpi, "value": str(int(n)), "target": tgt, "note": note})
    by = {r["kpi"]: r for r in rows}
    assert by[KPI_WRONG_N]["target"] == ""
    assert by[KPI_RETRY]["target"] == ""
    assert by[KPI_WRONG_N]["value"] == "2"
