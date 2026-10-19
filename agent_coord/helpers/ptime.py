"""UTC -> Pacific wall time for human-facing lines (PT label).

zoneinfo needs tzdata on Windows; fall back to the US DST rule
(second Sunday of March 02:00 local to first Sunday of November 02:00).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

_PT_ZONE = "America/Los_Angeles"


def _nth_sunday(year: int, month: int, n: int) -> datetime:
    d = datetime(year, month, 1)
    first = d + timedelta(days=(6 - d.weekday()) % 7)
    return first + timedelta(weeks=n - 1)


def _fallback_pt(utc_naive: datetime) -> datetime:
    y = utc_naive.year
    # DST starts 02:00 PST (10:00 UTC), ends 02:00 PDT (09:00 UTC).
    start = _nth_sunday(y, 3, 2) + timedelta(hours=10)
    end = _nth_sunday(y, 11, 1) + timedelta(hours=9)
    off = -7 if start <= utc_naive < end else -8
    return utc_naive + timedelta(hours=off)


def utc_to_pt(value: datetime | None, *, use_zoneinfo: bool = True) -> datetime | None:
    """Naive or aware UTC datetime -> naive Pacific datetime."""
    if value is None:
        return None
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    if use_zoneinfo:
        try:
            from zoneinfo import ZoneInfo

            return value.replace(tzinfo=timezone.utc).astimezone(ZoneInfo(_PT_ZONE)).replace(tzinfo=None)
        except Exception:
            pass
    return _fallback_pt(value)


def pt_label(value: datetime | None) -> str:
    """'2026-10-09 04:30 PT' from a UTC datetime; '' when None."""
    pt = utc_to_pt(value)
    if pt is None:
        return ""
    return pt.strftime("%Y-%m-%d %H:%M") + " PT"
