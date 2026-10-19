# -*- coding: utf-8 -*-
"""Default system SCORE, written when a verb finishes.

One score per desk on Office (kpi system). score.value is today's verb count.
mill_score_event holds one JSON document for the hour and one for the day:
verb counts, host milliseconds, and mail and todo bytes. At most 4096 bytes.
A larger document is rejected by mill_score_event and recorded on mill-perf.log.
A missing procedure leaves the verb alone.
"""
from __future__ import annotations

import os
import threading
import time
from datetime import datetime

from agent_coord.const import CONST_DESK, CONST_OFFICE

OFFICE = CONST_OFFICE
KPI = "system"
WALL_KPI = "wall"
KEEP_DAYS = 30
KEEP_BYTES = 4096
SPILL = "score history exceeds 4096 bytes"


def note_verb(
    desk: str,
    verb: str,
    *,
    req_b: int = 0,
    resp_b: int = 0,
    ms: float = 0.0,
    cn=None,
    now: datetime | None = None,
) -> None:
    """Record one finished verb. Swallows book errors so the reply still goes out."""
    own = False
    try:
        if cn is None:
            from agent_coord.server.records.db import connect

            cn = connect()
            own = True
        _note(cn, desk, verb, req_b=req_b, resp_b=resp_b, ms=ms, now=now)
    except Exception as e:
        text = str(e)
        if SPILL in text:
            _log_spill(desk, verb, text)
            return
        if getattr(e, "errno", None) in (1146, 1305) or "mill_score_event" in text or "score_evidence" in text:
            return
        try:
            from agent_coord.server.push import perf_log

            perf_log("score.system", 0, ok=0, err=text[:160])
        except Exception:
            pass
    finally:
        if own and cn is not None:
            try:
                cn.close()
            except Exception:
                pass


def _log_spill(desk: str, verb: str, text: str) -> None:
    try:
        from agent_coord.server.push import perf_log

        perf_log(
            "score.history",
            0,
            ok=0,
            desk=desk,
            verb=verb,
            err=text[:160],
        )
    except Exception:
        pass


def _n(value) -> int:
    try:
        n = int(round(float(value)))
    except (TypeError, ValueError):
        return 0
    return n if n > 0 else 0


def wall_route(path: str) -> str:
    """Wall /api path, without a query and without a row id. Empty for verbs and pages."""
    raw = (path or "").split("?", 1)[0].strip()
    if not raw.startswith("/api/") or raw.startswith("/api/mill"):
        return ""
    parts = [p for p in raw.split("/") if p]
    if len(parts) >= 4 and parts[1] == "v1":
        route = "/api/v1/" + parts[2]
    elif len(parts) >= 3 and parts[1] == "admin":
        route = "/api/admin/" + parts[2]
    else:
        route = "/" + "/".join(parts[:2])
    if len(route) > 64 or any(c in route for c in "\\\"'"):
        return ""
    return route


_wall_lock = threading.Lock()
_wall_q: list[tuple[str, float]] = []
_wall_started = False
_WALL_FLUSH_S = 1.0


def enqueue_wall(route: str, ms: float = 0.0) -> None:
    """Park one wall timing. The request returns before the book write."""
    route = wall_route(route)
    if not route:
        return
    with _wall_lock:
        _wall_q.append((route, float(ms)))
        _ensure_flusher()


_verb_q: list[tuple[str, str, int, int, float]] = []
_VERB_Q_MAX = 5000


def enqueue_verb(desk: str, verb: str, *, req_b: int = 0, resp_b: int = 0, ms: float = 0.0) -> None:
    """Park one finished verb for the flusher, so the reply goes out first (F24).

    The score lands within about a second, on one connection per batch. Under
    pytest (no flusher) the write happens here, as before.
    """
    if os.environ.get("PYTEST_CURRENT_TEST"):
        note_verb(desk, verb, req_b=req_b, resp_b=resp_b, ms=ms)
        return
    with _wall_lock:
        if len(_verb_q) >= _VERB_Q_MAX:
            del _verb_q[0]
        _verb_q.append((str(desk or ""), str(verb or ""), int(req_b or 0), int(resp_b or 0), float(ms or 0.0)))
        _ensure_flusher()


def flush_verbs() -> int:
    """Write parked verbs on one connection. Returns how many were attempted."""
    with _wall_lock:
        batch = list(_verb_q)
        _verb_q.clear()
    if not batch:
        return 0
    cn = None
    try:
        from agent_coord.server.records.db import connect

        cn = connect()
        for desk, verb, req_b, resp_b, ms in batch:
            note_verb(desk, verb, req_b=req_b, resp_b=resp_b, ms=ms, cn=cn)
    except Exception:
        return 0
    finally:
        if cn is not None:
            try:
                cn.close()
            except Exception:
                pass
    return len(batch)


def _ensure_flusher() -> None:
    global _wall_started
    if _wall_started:
        return
    # Tests drain the queue themselves so a background write misses a throwaway book.
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return
    _wall_started = True
    threading.Thread(target=_flush_loop, name="mill-wall-note", daemon=True).start()
    import atexit

    atexit.register(_flush_at_exit)


def _flush_at_exit() -> None:
    """A clean stop writes what is parked; a crash loses at most about a second."""
    for fn in (flush_wall, flush_verbs):
        try:
            fn()
        except Exception:
            pass


def _flush_loop() -> None:
    while True:
        time.sleep(_WALL_FLUSH_S)
        try:
            flush_wall()
        except Exception:
            pass
        try:
            flush_verbs()
        except Exception:
            pass


def flush_wall() -> int:
    """Write parked timings on one connection. Returns how many were attempted."""
    with _wall_lock:
        batch = list(_wall_q)
        _wall_q.clear()
    if not batch:
        return 0
    cn = None
    try:
        from agent_coord.server.records.db import connect

        cn = connect()
        for route, ms in batch:
            note_wall(route, ms, cn=cn)
    except Exception:
        return 0
    finally:
        if cn is not None:
            try:
                cn.close()
            except Exception:
                pass
    return len(batch)


def note_wall(route: str, ms: float = 0.0, *, cn=None, now: datetime | None = None) -> None:
    """Count one wall route on the single office score. A book error does not fail the page."""
    route = wall_route(route)
    if not route:
        return
    own = False
    try:
        if cn is None:
            from agent_coord.server.records.db import connect

            cn = connect()
            own = True
        _wall(cn, route, ms=ms, now=now)
    except Exception as e:
        text = str(e)
        if SPILL in text:
            _log_spill(OFFICE, route, text)
            return
        if getattr(e, "errno", None) in (1146, 1305) or "mill_wall_event" in text or "score_evidence" in text:
            return
        try:
            from agent_coord.server.push import perf_log

            perf_log("wall.api", 0, ok=0, err=text[:160])
        except Exception:
            pass
    finally:
        if own and cn is not None:
            try:
                cn.close()
            except Exception:
                pass


def _wall(cn, route: str, *, ms: float, now: datetime | None) -> None:
    from agent_coord.server.records.db import _run_proc, finish_cursor

    cur = cn.cursor()
    try:
        _run_proc(cur, "mill_wall_event", [route[:64], _n(ms), now])
    except Exception:
        try:
            cn.rollback()
        except Exception:
            pass
        raise
    finally:
        finish_cursor(cur)
        try:
            cur.close()
        except Exception:
            pass


def _note(cn, desk: str, verb: str, *, req_b: int, resp_b: int, ms: float, now: datetime | None) -> None:
    from agent_coord.client.outbound import canonical_verb
    from agent_coord.server.records.name import bare

    verb = canonical_verb(verb)
    who = bare((desk or "").strip(), CONST_DESK)
    if not verb or not who:
        return
    from agent_coord.server.records.db import _run_proc, finish_cursor

    cur = cn.cursor()
    try:
        _run_proc(cur, "mill_score_event", [who, verb, _n(ms), _n(req_b), _n(resp_b), now])
    except Exception:
        try:
            cn.rollback()
        except Exception:
            pass
        raise
    finally:
        finish_cursor(cur)
        try:
            cur.close()
        except Exception:
            pass
