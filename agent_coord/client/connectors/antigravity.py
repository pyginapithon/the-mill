"""Antigravity / Gemini CLI: mill here HINT then gemini or antigravity -p if on PATH."""
from __future__ import annotations

from typing import Any

from .spawn import skip_ping, spawn_cli

VENDOR = "antigravity"


def poke(hint: dict[str, Any]) -> None:
    if skip_ping(hint):
        return
    try:
        spawn_cli("gemini", ["-p"], hint)
        return
    except NotImplementedError:
        pass
    spawn_cli("antigravity", ["-p"], hint)
