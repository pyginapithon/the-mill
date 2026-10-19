"""Vendor poke after mill-wall fan-out. Spawn map first; vendor is leftover."""
from __future__ import annotations

from typing import Any, Callable

from . import antigravity, claude, grok_bot, grok_build, kimi, openai_agents
from .spawn import skip_ping, spawn_hint

CONNECTORS = {
    grok_build.VENDOR: grok_build.poke,
    grok_bot.VENDOR: grok_bot.poke,
    antigravity.VENDOR: antigravity.poke,
    claude.VENDOR: claude.poke,
    kimi.VENDOR: kimi.poke,
    openai_agents.VENDOR: openai_agents.poke,
}


def poke(vendor: str, hint: dict[str, Any]) -> None:
    if skip_ping(hint):
        return
    if spawn_hint(hint):
        return
    fn: Callable[[dict[str, Any]], None] | None = CONNECTORS.get((vendor or "").strip().lower())
    if fn is None:
        raise NotImplementedError(f"no mill connector for vendor={vendor!r}")
    fn(hint)
