# -*- coding: utf-8 -*-
"""A4 MAIL Threads SoR: stamp formula + score_tick scrape."""
from datetime import datetime, timezone
from pathlib import Path

from agent_coord.server import mail_sor as ms
from agent_coord.server.score_tick import (
    BOOK_PERF,
    BOOK_TARGET,
    KPI_MAIL_HIT,
    KPI_MAIL_REASK,
    measure,
    measure_mail_sor,
)


def setup_function() -> None:
    ms.reset_for_tests()


def test_book_mail_kpi_formula() -> None:
    assert KPI_MAIL_HIT in BOOK_PERF
    assert KPI_MAIL_REASK in BOOK_PERF
    assert BOOK_TARGET[KPI_MAIL_HIT] == ""
    assert BOOK_TARGET[KPI_MAIL_REASK] == ""
    assert KPI_MAIL_HIT == "mill-office.mail_hit_n"
    assert KPI_MAIL_REASK == "mill-office.mail_reask_n"
    assert "mail" in BOOK_PERF[KPI_MAIL_HIT].lower() or "thread" in BOOK_PERF[KPI_MAIL_HIT].lower()


def test_first_hit_then_reask(monkeypatch) -> None:
    lines: list[str] = []

    def fake_perf(op: str, ms_: float, **kv):
        parts = [f"op={op}", f"ms={ms_:.1f}"] + [f"{k}={v}" for k, v in kv.items()]
        lines.append(" ".join(parts))

    monkeypatch.setattr("agent_coord.server.push.perf_log", fake_perf)
    desk = "DESK_builder"
    envelope = {"id": 42, "thread": 1, "tree": "TREE_abc", "chain": [{"id": 42}]}
    body = {"mail_id": 42}
    ms.note_mail(desk, "mail-thread", envelope, body=body)
    assert len(lines) == 1
    assert "op=mail.hit" in lines[0]
    assert "mail=42" in lines[0]
    assert "reask=0" in lines[0]
    assert "desk=DESK_builder" in lines[0]
    assert ms.seen_snapshot(desk, 42) == 1
    ms.note_mail(desk, "mail-thread", envelope, body=body)
    assert len(lines) == 2
    assert "reask=1" in lines[1]
    assert ms.seen_snapshot(desk, 42) == 2


def test_off_tree_no_stamp(monkeypatch) -> None:
    lines: list[tuple] = []
    monkeypatch.setattr(
        "agent_coord.server.push.perf_log",
        lambda op, ms_, **kv: lines.append((op, ms_, kv)),
    )
    ms.note_mail(
        "DESK_a",
        "mail-thread",
        {"id": 7, "chain": [{"id": 7}]},  # no thread / tree
        body={"mail_id": 7},
    )
    assert lines == []


def test_tree_crumb_without_thread_flag_stamps(monkeypatch) -> None:
    lines: list[str] = []
    monkeypatch.setattr(
        "agent_coord.server.push.perf_log",
        lambda op, ms_, **kv: lines.append(f"op={op} reask={kv.get('reask')}"),
    )
    ms.note_mail(
        "DESK_a",
        "mail-thread",
        {"id": 9, "tree": "TREE_x", "chain": [{"id": 9}]},
        body={"mail_id": 9},
    )
    assert len(lines) == 1
    assert "reask=0" in lines[0]


def test_inbox_and_other_commands_skipped(monkeypatch) -> None:
    lines: list[tuple] = []
    monkeypatch.setattr(
        "agent_coord.server.push.perf_log",
        lambda op, ms_, **kv: lines.append((op, ms_, kv)),
    )
    ms.note_mail("DESK_a", "inbox", [{"id": 1}], body={})
    ms.note_mail("DESK_a", "thread", {"ok": True}, body={"mail_id": 1})
    # no mail_id in body or envelope
    ms.note_mail("DESK_a", "mail-thread", {"thread": 1, "chain": []}, body={})
    assert lines == []


def test_envelope_id_fallback_without_body_mail_id(monkeypatch) -> None:
    lines: list[str] = []
    monkeypatch.setattr(
        "agent_coord.server.push.perf_log",
        lambda op, ms_, **kv: lines.append(f"op={op} mail={kv.get('mail')}"),
    )
    ms.note_mail(
        "DESK_a",
        "mail-thread",
        {"id": 77, "thread": 1, "chain": [{"id": 77}]},
        body={},
    )
    assert len(lines) == 1
    assert "mail=77" in lines[0]


def test_measure_mail_sor_counts() -> None:
    text = "\n".join(
        [
            "2026-09-27T10:00:00Z op=mail.hit ms=0.0 mail=42 desk=DESK_a reask=0 ok=1",
            "2026-09-27T10:00:01Z op=mail.hit ms=0.0 mail=42 desk=DESK_a reask=1 ok=1",
            "2026-09-27T10:00:02Z op=mail.hit ms=0.0 mail=99 desk=DESK_b reask=0 ok=1",
            "2026-09-27T09:00:00Z op=mail.hit ms=0.0 mail=1 desk=DESK_old reask=1 ok=1",
        ]
    )
    since = datetime(2026, 9, 27, 9, 30, 0, tzinfo=timezone.utc)
    assert measure_mail_sor(text, since) == (3, 1)


def test_measure_includes_mail_kpis(tmp_path: Path) -> None:
    (tmp_path / "mill-perf.log").write_text(
        "2026-09-27T10:00:00Z op=mail.hit ms=0.0 mail=56 desk=DESK_x reask=1 ok=1\n",
        encoding="utf-8",
    )
    now = datetime(2026, 9, 27, 10, 30, 0, tzinfo=timezone.utc)
    row = measure(dest=tmp_path, window_s=3600, now=now)
    assert row[KPI_MAIL_HIT] == 1
    assert row[KPI_MAIL_REASK] == 1


def test_publish_book_perf_mail_empty_target() -> None:
    from agent_coord.server import score_tick as st

    for kpi in (KPI_MAIL_HIT, KPI_MAIL_REASK):
        assert st.BOOK_TARGET.get(kpi, st.TARGET) == ""
