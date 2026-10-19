"""Unit tests for maintenance drain (pure; no live mill / MySQL).

SoR: docs/acceptance/ACCEPTANCE-MILL-MAINTENANCE-DRAIN.md
JOB: mill-maintenance-drain
"""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from agent_coord.protocol.presence.drain import (
    CANCEL_MARKER,
    MARKER,
    PHASE2_CAP_S,
    PHASE2_NEVER_S,
    PHASE2_START_S,
    drain_wall_phase,
    extract_drain_from_records,
    format_maintenance_drain_body,
    parse_maintenance_drain,
    phase1_sleep_s,
    phase2_backoff_s,
)


def test_parse_maintenance_drain_requires_eta():
    assert parse_maintenance_drain("hello") is None
    assert parse_maintenance_drain(MARKER) is None
    assert parse_maintenance_drain(f"{MARKER} reason=x") is None


def test_parse_maintenance_drain_ok():
    body = format_maintenance_drain_body(
        "2026-09-12T12:00:00",
        reason="reboot",
        down_for_s=600,
        drain_id="d1",
    )
    assert MARKER in body
    assert len(body) <= 500
    got = parse_maintenance_drain(body)
    assert got is not None
    assert got["eta_at"] == datetime(2026, 9, 12, 12, 0, 0)
    assert got["reason"] == "reboot"
    assert got["down_for_s"] == 600
    assert got["drain_id"] == "d1"


def test_parse_iso_z_and_host_local():
    z = parse_maintenance_drain(f"{MARKER} eta_at=2026-09-12T12:00:00Z")
    assert z is not None
    assert z["eta_at"] == datetime(2026, 9, 12, 12, 0, 0)
    local = parse_maintenance_drain(f"{MARKER} eta_at=2026-09-12 12:00:00")
    assert local is not None
    assert local["eta_at"] == datetime(2026, 9, 12, 12, 0, 0)


def test_cancel_marker_parked_not_required():
    # CANCEL alone is not a drain parse; cancel not required this JOB
    assert parse_maintenance_drain(CANCEL_MARKER) is None
    assert parse_maintenance_drain(f"{CANCEL_MARKER} eta_at=2026-09-12T12:00:00") is None


def test_phase1_sleep_until_eta_no_expo():
    now = datetime(2026, 9, 12, 11, 0, 0)
    eta = datetime(2026, 9, 12, 12, 0, 0)
    s = phase1_sleep_s(eta, now, skew_s=10)
    assert s == 3600 - 10
    # past eta -> 0 (no busy loop / no expo)
    assert phase1_sleep_s(eta, eta + timedelta(seconds=1), skew_s=10) == 0.0
    # skew clamped 5..15
    assert phase1_sleep_s(eta, now, skew_s=1) == 3600 - 5
    assert phase1_sleep_s(eta, now, skew_s=100) == 3600 - 15


def test_phase2_backoff_5_to_120_jitter_never_3600():
    # deterministic mid jitter (0.5 -> factor 1.0)
    rng = lambda: 0.5
    assert phase2_backoff_s(0, rng=rng) == PHASE2_START_S
    assert phase2_backoff_s(1, rng=rng) == 10.0
    assert phase2_backoff_s(2, rng=rng) == 20.0
    assert phase2_backoff_s(3, rng=rng) == 40.0
    assert phase2_backoff_s(4, rng=rng) == 80.0
    assert phase2_backoff_s(5, rng=rng) == PHASE2_CAP_S
    assert phase2_backoff_s(20, rng=rng) == PHASE2_CAP_S
    # jitter extremes still well under 1h
    lo = phase2_backoff_s(0, rng=lambda: 0.0)
    hi = phase2_backoff_s(0, rng=lambda: 1.0)
    assert 4.0 <= lo <= 5.0
    assert 5.0 <= hi <= 6.0
    for attempt in range(0, 30):
        for j in (0.0, 0.5, 1.0):
            v = phase2_backoff_s(attempt, rng=lambda j=j: j)
            assert v < PHASE2_NEVER_S
            assert v <= PHASE2_CAP_S * 1.2 + 0.01


def test_drain_wall_phase_and_extract():
    now = datetime(2026, 9, 12, 11, 0, 0)
    eta = datetime(2026, 9, 12, 12, 0, 0)
    assert drain_wall_phase(eta, now) == "draining"
    assert drain_wall_phase(eta, eta) == "overdue"
    assert drain_wall_phase(eta, eta + timedelta(seconds=1)) == "overdue"
    mail = [
        {"id": 1, "body": f"{MARKER} eta_at=2026-09-12T11:30:00 reason=old"},
        {"id": 9, "body": f"{MARKER} eta_at=2026-09-12T12:00:00 reason=new"},
    ]
    got = extract_drain_from_records(mailbox=mail, now=now)
    assert got is not None
    assert got["eta_at"].startswith("2026-09-12T12:00:00")
    assert got["phase"] == "draining"
    assert got["reason"] == "new"
    assert got["cancel_parked"] is True
    ev = [{"id": 3, "kind": "maintenance_drain", "detail": f"{MARKER} eta_at=2026-09-12T12:00:00"}]
    got2 = extract_drain_from_records(events=ev, now=eta + timedelta(minutes=1))
    assert got2 is not None
    assert got2["phase"] == "overdue"


def test_body_cap_500():
    body = format_maintenance_drain_body(
        "2026-09-12T12:00:00",
        reason="x" * 600,
        down_for_s=10,
        drain_id="abc",
    )
    assert len(body) <= 500
    assert parse_maintenance_drain(body) is not None
