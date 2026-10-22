# -*- coding: utf-8 -*-
"""MAIL Threads SoR stamp: mail-thread hit + re-ask same mail_id (A4).

In-process per-(desk, mail_id) memory. On mill mail-thread peek of one
TREE-backed mail, emit ``op=mail.hit`` (reask=0 first, reask=1 later).
score_tick counts hits / reasks into opt-in book KPIs (no Wall chrome).
"""
from __future__ import annotations

import threading
from typing import Any

KPI_MAIL_HIT = "mill-office.mail_hit_n"
KPI_MAIL_REASK = "mill-office.mail_reask_n"
BOOK_PERF: dict[str, str] = {
    KPI_MAIL_HIT: (
        "count mill mail-thread Threads SoR peeks (TREE-backed) in window (book); informational"
    ),
    KPI_MAIL_REASK: (
        "count Threads SoR re-asks of same mail_id in window (book); informational"
    ),
}

_lock = threading.Lock()
# (desk, mail_id) -> hit_count so far
_seen: dict[tuple[str, int], int] = {}


def _who(desk: str) -> str:
    return str(desk or "").strip()


def note_mail(
    desk: str | None,
    command: str,
    result: Any,
    *,
    body: dict[str, Any] | None = None,
) -> None:
    """Stamp mail.hit when mill mail-thread peeks one TREE-backed mail.

    Formula:
    - command must be mail-thread
    - body must carry mail_id / id
    - result is a dict with thread truthy (TREE-backed envelope)
    - first (desk, mail_id) -> reask=0; later -> reask=1
    """
    v = (command or "").strip().lower()
    if v != "mail-thread":
        return
    body = body or {}
    try:
        mid = int(body.get("mail_id") or body.get("id") or 0)
    except (TypeError, ValueError):
        mid = 0
    if not mid and isinstance(result, dict):
        try:
            mid = int(result.get("id") or result.get("mail_id") or 0)
        except (TypeError, ValueError):
            mid = 0
    if mid <= 0:
        return
    if not isinstance(result, dict):
        return
    thread_flag = result.get("thread")
    if not thread_flag or thread_flag in (0, "0", False):
        # Fallback: TREE crumbs on envelope mean Threads-backed.
        if not result.get("tree"):
            return
    who = _who(desk or "")
    if not who:
        return
    key = (who, mid)
    with _lock:
        prior = int(_seen.get(key) or 0)
        _seen[key] = prior + 1
        reask = 1 if prior > 0 else 0
    try:
        from agent_coord.server.push import perf_log

        perf_log(
            "mail.hit",
            0.0,
            mail=mid,
            desk=who,
            reask=reask,
            ok=1,
        )
    except Exception:
        pass


def reset_for_tests() -> None:
    """Test helper: clear in-process hit memory."""
    with _lock:
        _seen.clear()


def seen_snapshot(desk: str, mail_id: int) -> int:
    """Test helper: hit count recorded for desk+mail."""
    who = _who(desk)
    with _lock:
        return int(_seen.get((who, int(mail_id))) or 0)
