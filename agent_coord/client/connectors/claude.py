"""Claude Code: mill here HINT then `claude -p` when claude is on PATH."""
from __future__ import annotations

from typing import Any

from .spawn import skip_ping, spawn_cli

VENDOR = "claude"


def poke(hint: dict[str, Any]) -> None:
    if skip_ping(hint):
        return
    spawn_cli("claude", ["-p"], hint)
