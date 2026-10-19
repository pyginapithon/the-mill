"""Maintenance drain / server going-down helpers (pure).

SoR: docs/acceptance/ACCEPTANCE-MILL-MAINTENANCE-DRAIN.md
JOB: mill-maintenance-drain

Broadcast marker MAINTENANCE_DRAIN + required eta_at.
Two-phase reconnect: sleep-until-eta (phase1), then 5s*2 cap 120s jitter (phase2).
MAINTENANCE_CANCEL is PARKED this JOB (escape: Ctrl+C / new presence).
"""
from __future__ import annotations

import random
import re
from datetime import datetime, timedelta
from typing import Any, Callable, Mapping

MARKER = "MAINTENANCE_DRAIN"
CANCEL_MARKER = "MAINTENANCE_CANCEL"  # PARKED this JOB
EVENT_KIND = "maintenance_drain"

PHASE1_SKEW_S_DEFAULT = 10.0
PHASE1_SKEW_S_MIN = 5.0
PHASE1_SKEW_S_MAX = 15.0

PHASE2_START_S = 5.0
PHASE2_FACTOR = 2.0
PHASE2_CAP_S = 120.0
PHASE2_JITTER = 0.20  # +/-20%
PHASE2_SOFT_LOG_EVERY = 10
PHASE2_NEVER_S = 3600.0  # must never stretch to 1h probes

_KV = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)=(\S+)")


def _naive(dt: datetime) -> datetime:
    return dt.replace(tzinfo=None) if getattr(dt, "tzinfo", None) else dt


def parse_iso_eta(raw: str | None) -> datetime | None:
    """Parse eta_at ISO (host-local or Z). Returns naive datetime or None."""
    s = (raw or "").strip()
    if not s:
        return None
    t = s.replace("Z", "+00:00") if s.endswith("Z") else s
    try:
        dt = datetime.fromisoformat(t)
    except ValueError:
        # space-separated fallback
        try:
            dt = datetime.fromisoformat(s.replace("T", " ").replace("Z", "").split("+")[0].strip())
        except ValueError:
            return None
    return _naive(dt)


def format_maintenance_drain_body(
    eta_at: str | datetime,
    *,
    reason: str = "",
    down_for_s: int | None = None,
    drain_id: str = "",
) -> str:
    """Build MAIL body (<=500) with MAINTENANCE_DRAIN marker + required eta_at."""
    if isinstance(eta_at, datetime):
        eta_s = _naive(eta_at).isoformat(timespec="seconds")
    else:
        eta_s = str(eta_at).strip()
        if not eta_s:
            raise ValueError("eta_at required")
        if parse_iso_eta(eta_s) is None:
            raise ValueError("eta_at must be ISO datetime")
    parts = [MARKER, f"eta_at={eta_s}"]
    if down_for_s is not None:
        parts.append(f"down_for_s={int(down_for_s)}")
    rid = (drain_id or "").strip()
    if rid:
        parts.append(f"drain_id={rid[:64]}")
    why = (reason or "").strip().replace("\n", " ")
    if why:
        # keep body under 500; reason last so it can truncate
        head = " ".join(parts) + " reason="
        room = 500 - len(head)
        if room < 1:
            return " ".join(parts)[:500]
        parts.append("reason=" + why[:room])
    body = " ".join(parts)
    return body[:500]


def parse_maintenance_drain(body: str | None) -> dict[str, Any] | None:
    """Parse MAINTENANCE_DRAIN MAIL body. None if marker missing or eta_at invalid.

    CANCEL marker alone does not parse as drain (CANCEL PARKED this JOB).
    """
    text = (body or "").strip()
    if not text or MARKER not in text:
        return None
    # Prefer the drain segment; ignore cancel-only bodies.
    fields: dict[str, str] = {}
    for m in _KV.finditer(text):
        fields[m.group(1)] = m.group(2)
    # eta_at may be "YYYY-MM-DD HH:MM:SS" (space); \S+ KV would truncate at space.
    eta_m = re.search(
        r"eta_at=("
        r"\d{4}-\d{2}-\d{2}"
        r"(?:[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)?"
        r")",
        text,
    )
    eta_raw = (eta_m.group(1) if eta_m else fields.get("eta_at") or "").strip()
    eta = parse_iso_eta(eta_raw)
    if eta is None:
        return None
    out: dict[str, Any] = {
        "marker": MARKER,
        "eta_at": eta,
        "eta_at_raw": eta_raw,
        "reason": fields.get("reason", ""),
        "drain_id": fields.get("drain_id", ""),
        "down_for_s": None,
    }
    if "down_for_s" in fields:
        try:
            out["down_for_s"] = int(fields["down_for_s"])
        except ValueError:
            out["down_for_s"] = None
    return out


def phase1_sleep_s(
    eta_at: datetime,
    now: datetime | None = None,
    *,
    skew_s: float = PHASE1_SKEW_S_DEFAULT,
) -> float:
    """Seconds to sleep until eta_at - skew. Never busy-loop (0 if already past)."""
    now = _naive(now or datetime.now())
    eta = _naive(eta_at)
    skew = max(PHASE1_SKEW_S_MIN, min(PHASE1_SKEW_S_MAX, float(skew_s)))
    target = eta - timedelta(seconds=skew)
    return max(0.0, (target - now).total_seconds())


def phase2_backoff_s(
    attempt: int,
    *,
    start_s: float = PHASE2_START_S,
    factor: float = PHASE2_FACTOR,
    cap_s: float = PHASE2_CAP_S,
    jitter: float = PHASE2_JITTER,
    rng: Callable[[], float] | None = None,
) -> float:
    """Expo backoff start*2^attempt capped; +/-jitter. Never returns >= 3600s."""
    n = max(0, int(attempt))
    base = float(start_s) * (float(factor) ** n)
    base = min(float(cap_s), base)
    pick = rng if rng is not None else random.random
    j = 1.0 + float(jitter) * (2.0 * float(pick()) - 1.0)
    out = max(0.1, base * j)
    # Hard ceiling: never hourly laziness
    hard = float(cap_s) * (1.0 + float(jitter))
    out = min(out, hard)
    if out >= PHASE2_NEVER_S:
        out = float(cap_s)
    return out


def drain_wall_phase(eta_at: datetime, now: datetime | None = None) -> str:
    """Wall phase: 'draining' until eta, 'overdue' after."""
    now = _naive(now or datetime.now())
    eta = _naive(eta_at)
    return "draining" if now < eta else "overdue"


def drain_public_dict(parsed: Mapping[str, Any], now: datetime | None = None) -> dict[str, Any]:
    """JSON-safe maintenance object for floor / Wall."""
    eta = parsed.get("eta_at")
    if isinstance(eta, datetime):
        eta_s = _naive(eta).isoformat(timespec="seconds")
        phase = drain_wall_phase(eta, now)
    else:
        eta_s = str(parsed.get("eta_at_raw") or eta or "")
        dt = parse_iso_eta(eta_s)
        phase = drain_wall_phase(dt, now) if dt else "draining"
    return {
        "marker": MARKER,
        "eta_at": eta_s,
        "phase": phase,
        "reason": str(parsed.get("reason") or ""),
        "drain_id": str(parsed.get("drain_id") or ""),
        "down_for_s": parsed.get("down_for_s"),
        "cancel_parked": True,
        "escape": "Ctrl+C / new presence start (MAINTENANCE_CANCEL PARKED)",
    }


def extract_drain_from_records(
    *,
    mailbox: list[Mapping[str, Any]] | None = None,
    events: list[Mapping[str, Any]] | None = None,
    now: datetime | None = None,
) -> dict[str, Any] | None:
    """Newest active drain from MAIL bodies and/or agent_event rows.

    Prefer newest by id/at among parsed MAINTENANCE_DRAIN / kind=maintenance_drain.
    """
    candidates: list[tuple[Any, dict[str, Any]]] = []
    for row in mailbox or []:
        parsed = parse_maintenance_drain(str(row.get("body") or ""))
        if not parsed:
            continue
        key = row.get("id") or row.get("at") or 0
        candidates.append((key, parsed))
    for row in events or []:
        kind = str(row.get("kind") or "")
        detail = str(row.get("detail") or "")
        if kind == EVENT_KIND or MARKER in detail:
            parsed = parse_maintenance_drain(detail if MARKER in detail else f"{MARKER} {detail}")
            if not parsed and kind == EVENT_KIND:
                # detail may be eta-only; try wrap
                parsed = parse_maintenance_drain(f"{MARKER} {detail}".strip())
            if not parsed:
                continue
            key = row.get("id") or row.get("at") or 0
            candidates.append((key, parsed))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0])
    newest = candidates[-1][1]
    return drain_public_dict(newest, now)


def maintenance_banner_html(maint: Mapping[str, Any] | None) -> str:
    """Wall banner HTML for intentional drain (not false API-down)."""
    if not maint:
        return ""
    eta = str(maint.get("eta_at") or "")
    phase = str(maint.get("phase") or "draining")
    reason = str(maint.get("reason") or "").strip()
    why = f" {reason}" if reason else ""
    if phase == "overdue":
        return (
            f"<b>maintenance overdue.</b> ETA was {eta}.{why} "
            "Desks reconnecting (<=120s cadence). Not a surprise API outage."
        )
    return (
        f"<b>maintenance / draining.</b> ETA {eta}.{why} "
        "Desks sleep until ETA, then reconnect. Not false API-down."
    )
