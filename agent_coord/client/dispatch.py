# -*- coding: utf-8 -*-
"""Desk-side HINT dispatch. One frame, one choice.

A route hit runs that program (the desk may be busy; this does not wait).
No route wakes the vendor agent. An empty route value does neither.
The frame is the small Hub push: no token, no letter, no card body.
"""
from __future__ import annotations

import json
import threading
from typing import Any

DETAIL_MAX = 4096
_KEEP = ("type", "id", "hint", "detail", "desk", "route", "verb", "idem", "kind")
_SEEN: set[str] = set()
_SEEN_MAX = 4096
_SEEN_LOCK = threading.Lock()


def _secret_key(key: str) -> bool:
    s = str(key or "").lower().replace("-", "_")
    if s in {"token", "authorization", "password", "secret", "bearer", "cookie", "access_token"}:
        return True
    return s.endswith("_token") or "password" in s


def _cap_detail(detail: Any) -> Any:
    if isinstance(detail, str):
        return detail[:DETAIL_MAX]
    if isinstance(detail, dict):
        clean = {k: v for k, v in detail.items() if not _secret_key(str(k))}
        raw = json.dumps(clean, default=str, separators=(",", ":"))
        if len(raw) <= DETAIL_MAX:
            return clean
        return raw[:DETAIL_MAX]
    return detail


def public_frame(msg: dict[str, Any] | None, desk: str = "") -> dict[str, Any]:
    """Fields a redirector or wake may see. Drops secrets and unknown keys."""
    src = dict(msg or {})
    out: dict[str, Any] = {}
    for key in _KEEP:
        if key not in src or src[key] is None:
            continue
        if key == "detail":
            out["detail"] = _cap_detail(src[key])
        elif key == "desk":
            continue
        elif _secret_key(key):
            continue
        else:
            out[key] = src[key]
    who = (desk or str(src.get("desk") or "")).strip()
    if who:
        out["desk"] = who.strip()
    return out


def _duplicate(frame: dict[str, Any]) -> bool:
    """True when this process already handled the poke's idempotency key."""
    key = str(frame.get("idem") or "").strip()
    if not key:
        return False
    with _SEEN_LOCK:
        if key in _SEEN:
            return True
        if len(_SEEN) >= _SEEN_MAX:
            _SEEN.clear()
        _SEEN.add(key)
        return False


def _log_field(raw: object) -> str:
    """One mill-perf field. Spaces would split the line."""
    text = str(raw or "").replace("\n", " ").replace("\r", " ").strip()
    return text.replace(" ", "_")[:80]


def _stamp_dispatch(decision: str, frame: dict[str, Any], vendor: str = "") -> None:
    """A7 stamp. One line, no duration field: op=hint.dispatch decision= key= idem= vendor=."""
    try:
        from agent_coord.client.route_chain import route_key
        from agent_coord.server.push import dest_log

        dest_log(
            "mill-perf.log",
            "op=hint.dispatch decision=%s key=%s idem=%s vendor=%s"
            % (
                _log_field(decision),
                _log_field(route_key(frame)),
                _log_field(frame.get("idem")),
                _log_field(vendor),
            ),
        )
    except Exception:
        pass


def dispatch_hint(desk: str, msg: dict[str, Any]) -> str:
    """work | wake | suppress | skip.

    work: a redirector handled the frame. The vendor does not run.
    wake: every redirector returned next. Vendor poke.
    suppress: an empty route value stopped the chain.
    skip: PING, a JOIN with no route (chart: ignore, no vendor poke),
    a repeated idempotency key, or this desk's HINT filter file (want) said no.
    The idempotency key is checked before the chain. PING never enters it.
    Each return appends one hint.dispatch line to mill-perf.log.
    """
    frame = public_frame(msg, desk)
    hint = str(frame.get("hint") or "")

    def finish(decision: str, vendor: str = "") -> str:
        _stamp_dispatch(decision, frame, vendor)
        return decision

    if hint == "PING":
        return finish("skip")
    from agent_coord.client.watch_filter import wants

    if not wants(desk, frame):
        return finish("skip")
    if _duplicate(frame):
        return finish("skip")
    from agent_coord.client.route_chain import try_route

    decision = try_route(desk, frame)
    if decision == "handled":
        from agent_coord.client.vendor import session_vendor

        return finish("work", session_vendor() or "")
    if decision == "suppress":
        return finish("suppress")
    if hint == "JOIN":
        return finish("skip")
    from agent_coord.client.connectors import poke
    from agent_coord.client.vendor import session_vendor

    vendor = session_vendor() or "grok-build"
    _stamp_dispatch("wake", frame, vendor)
    poke(vendor, frame)
    return "wake"
