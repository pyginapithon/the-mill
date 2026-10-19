"""Desk owner and hold-pid checks. No SQL."""

from __future__ import annotations

import os

from agent_coord.helpers.ident import slug
from agent_coord.lib.proc import holder_dead


def default_owner() -> str:
    env = (os.environ.get("AGENT_COORD_OWNER") or "").strip()
    if env:
        return slug(env)
    return f"pid-{os.getpid()}"


def holder_gone(pid, start, host=None) -> bool:
    """OS pid only. join has no pid column."""
    return holder_dead(pid, start)
