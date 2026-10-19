# -*- coding: utf-8 -*-
"""Nest SoR stamp: todo peek hit + re-ask same todo_id (A3).

In-process per-(desk, todo_id) memory. On mill todo peek of one TREE-backed
card, emit ``op=nest.hit`` (reask=0 first, reask=1 later). score_tick counts
hits / reasks into opt-in book KPIs (no Wall chrome, no always-on tax).
"""
from __future__ import annotations

import threading
from typing import Any

KPI_NEST_HIT = "mill-office.nest_hit_n"
KPI_NEST_REASK = "mill-office.nest_reask_n"
BOOK_PERF: dict[str, str] = {
    KPI_NEST_HIT: (
        "count mill todo Nest SoR peeks (TREE-backed card) in window (book); informational"
    ),
    KPI_NEST_REASK: (
        "count Nest SoR re-asks of same todo_id in window (book); informational"
    ),
}

_lock = threading.Lock()
# (desk, todo_id) -> hit_count so far (before current stamp)
_seen: dict[tuple[str, int], int] = {}


def _who(desk: str) -> str:
    return str(desk or "").strip()


def _need_of(card: dict[str, Any], body: dict[str, Any] | None) -> str:
    from agent_coord.helpers.ident import slug

    for src in (card, body or {}):
        if not isinstance(src, dict):
            continue
        for k in ("need_id", "need"):
            raw = src.get(k)
            if raw is not None and str(raw).strip():
                return slug(str(raw))
    return ""


def note_nest(
    desk: str | None,
    verb: str,
    result: Any,
    *,
    body: dict[str, Any] | None = None,
) -> None:
    """Stamp nest.hit when mill todo peeks one TREE-backed card.

    Formula:
    - verb must be todo
    - body must carry a need/need_id (single-card ask; board list skipped)
    - result is a one-element list (or dict) with nest truthy / nest=1
    - first (desk, todo_id) -> reask=0; later -> reask=1
    """
    v = (verb or "").strip().lower()
    if v != "todo":
        return
    body = body or {}
    raw_need = str(body.get("need") or body.get("need_id") or "").strip()
    if not raw_need:
        return
    card: dict[str, Any] | None = None
    if isinstance(result, list):
        if len(result) != 1 or not isinstance(result[0], dict):
            return
        card = result[0]
    elif isinstance(result, dict):
        card = result
    else:
        return
    nest_flag = card.get("nest")
    if not nest_flag or nest_flag in (0, "0", False):
        return
    try:
        todo_id = int(card.get("id") or 0)
    except (TypeError, ValueError):
        return
    if todo_id <= 0:
        return
    who = _who(desk or "")
    if not who:
        return
    need = _need_of(card, body)
    key = (who, todo_id)
    with _lock:
        prior = int(_seen.get(key) or 0)
        _seen[key] = prior + 1
        reask = 1 if prior > 0 else 0
    try:
        from agent_coord.server.push import perf_log

        perf_log(
            "nest.hit",
            0.0,
            todo=todo_id,
            need=need or "",
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


def seen_snapshot(desk: str, todo_id: int) -> int:
    """Test helper: hit count recorded for desk+todo."""
    who = _who(desk)
    with _lock:
        return int(_seen.get((who, int(todo_id))) or 0)
