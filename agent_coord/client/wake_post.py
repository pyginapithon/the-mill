# -*- coding: utf-8 -*-
"""A webhook POST is one desk frame. Same chain as a sit. The hub does not walk it."""
from __future__ import annotations

from typing import Any


def accept_wake(body: dict[str, Any] | None, desk: str = "") -> str:
    """Run dispatch_hint for this desk. Skip when the desk is missing."""
    who = str(desk or (body or {}).get("desk") or "").strip()
    if not who or not isinstance(body, dict):
        return "skip"
    from agent_coord.client.dispatch import dispatch_hint

    return dispatch_hint(who, body)
