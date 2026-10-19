# -*- coding: utf-8 -*-
"""Hold wait stamp: deny -> acquire blocked ms (A5 hold-blocked).

In-process per-(desk, resource) clock from mill hold ok=False (held by
another). When the same desk later acquires (ok=True), emit one mill-perf
line ``op=hold.blocked`` (ms + desk + resource + holder). score_tick sums
ms= into opt-in book KPI (no Wall chrome, no always-on Server-Timing).
"""
from __future__ import annotations

import threading
import time
from typing import Any

KPI_HOLD_BLOCKED_MS = "mill-office.hold_blocked_ms"
BOOK_PERF: dict[str, str] = {
    KPI_HOLD_BLOCKED_MS: (
        "sum ms desk wait behind mill hold mutex deny->acquire (book); informational"
    ),
}

_lock = threading.Lock()
# (desk, resource_slug) -> {t0, holder, stamped}
_waits: dict[tuple[str, str], dict[str, Any]] = {}


def _who(desk: str) -> str:
    return str(desk or "").strip()


def _res_of(result: Any, body: dict[str, Any] | None) -> str:
    raw = ""
    for src in (result, body or {}):
        if not isinstance(src, dict):
            continue
        for k in ("resource", "res"):
            v = src.get(k)
            if v is not None and str(v).strip():
                raw = str(v).strip()
                break
        if raw:
            break
    return raw


def _holder_of(result: Any) -> str:
    if not isinstance(result, dict):
        return ""
    return _who(str(result.get("owner") or result.get("holder") or ""))


def note_hold(
    desk: str | None,
    verb: str,
    result: Any,
    *,
    body: dict[str, Any] | None = None,
) -> None:
    """Track hold deny/acquire; on acquire after deny emit hold.blocked once.

    Formula:
    - hold ok=False starts (or keeps) wait for (desk, resource); records holder
    - hold ok=True after a wait stamps ms= and clears
    - hold ok=True with no prior wait: noop
    - non-hold verbs ignored
    """
    v = (verb or "").strip().lower()
    if v != "hold":
        return
    if not isinstance(result, dict):
        return
    who = _who(desk or "")
    if not who:
        return
    res = _res_of(result, body)
    if not res:
        return
    raw_ok = result.get("ok", True)
    if isinstance(raw_ok, bool):
        acquired = raw_ok
    else:
        try:
            acquired = int(raw_ok) == 1
        except (TypeError, ValueError):
            acquired = bool(raw_ok)
    key = (who, res)
    stamp: dict[str, Any] | None = None
    with _lock:
        if not acquired:
            holder = _holder_of(result) or ""
            row = _waits.get(key)
            if row is None or row.get("stamped"):
                _waits[key] = {
                    "t0": time.perf_counter(),
                    "holder": holder,
                    "stamped": False,
                }
            else:
                if holder:
                    row["holder"] = holder
            return
        # acquired
        row = _waits.get(key)
        if not row or row.get("stamped"):
            return
        t0 = float(row.get("t0") or time.perf_counter())
        ms = max(0.0, (time.perf_counter() - t0) * 1000.0)
        holder = str(row.get("holder") or _holder_of(result) or "")
        row["stamped"] = True
        stamp = {
            "ms": ms,
            "desk": who,
            "resource": res,
            "holder": holder,
        }
        _waits.pop(key, None)
    if stamp is None:
        return
    try:
        from agent_coord.server.push import perf_log

        perf_log(
            "hold.blocked",
            float(stamp["ms"]),
            desk=stamp["desk"],
            resource=stamp["resource"],
            holder=stamp["holder"],
            ok=1,
        )
    except Exception:
        pass


def reset_for_tests() -> None:
    """Test helper: clear in-process wait sessions."""
    with _lock:
        _waits.clear()


def wait_snapshot(desk: str, resource: str) -> dict[str, Any] | None:
    """Test helper: copy of wait row by desk + resource."""
    who = _who(desk)
    res = str(resource or "").strip()
    if not who or not res:
        return None
    with _lock:
        row = _waits.get((who, res))
        if not row:
            return None
        return dict(row)
