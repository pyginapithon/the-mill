# -*- coding: utf-8 -*-
"""HINT spawn map: mill connect starts an agent-supplied program.

skill.md is the chat HINT map. This is mill connect: route_key -> program,
HINT JSON on stdin. PING is never spawned.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any


def skip_ping(hint: dict[str, Any]) -> bool:
    return str(hint.get("hint") or "") == "PING"


def route_key(hint: dict[str, Any]) -> str:
    return f"{hint.get('type') or ''}:{hint.get('hint') or ''}"


def spawn_prompt(hint: dict[str, Any]) -> str:
    return (
        f"mill HINT {hint!r}. mill inbox --limit 3 or mill todo. "
        "Do not dump /api/floor. Prefer mill."
    )


def spawn_path(desk: str) -> Path:
    from agent_coord.client.offices import desk_local_file
    from agent_coord.config import mill_home
    from agent_coord.helpers.ident import desk as slug_desk

    hosted = desk_local_file(desk, "spawn")
    if hosted is not None:
        return hosted
    dest = mill_home() / "session"
    dest.mkdir(parents=True, exist_ok=True)
    return dest / f"{slug_desk(desk)}.spawn"


def _unquote(val: str) -> str:
    s = val.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        return s[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    return s


def load_map(desk: str) -> dict[str, str]:
    """<desk>.spawn: route_key = program. Re-read every HINT."""
    out: dict[str, str] = {}
    try:
        path = spawn_path(desk)
    except Exception:
        return out
    if not path.is_file():
        return out
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return out
    for line in lines:
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        key, raw = s.split("=", 1)
        out[key.strip()] = _unquote(raw)
    return out


def _catchall() -> str:
    env = (os.environ.get("AGENT_COORD_SPAWN") or "").strip()
    if env:
        return env
    try:
        from agent_coord.config import settings

        s = settings()
        for key in ("spawn", "bot_wake_cmd"):
            got = str(s.get(key) or "").strip()
            if got:
                return got
    except Exception:
        pass
    return (os.environ.get("AGENT_COORD_BOT_WAKE_CMD") or "").strip()


def program_for(hint: dict[str, Any]) -> str:
    """First hit: AGENT_COORD_SPAWN, then map route_key, then map *, then settings."""
    if skip_ping(hint):
        return ""
    env = (os.environ.get("AGENT_COORD_SPAWN") or "").strip()
    if env:
        return env
    desk = str(hint.get("desk") or os.environ.get("AGENT_COORD_OWNER") or "")
    mp = load_map(desk) if desk else {}
    hit = mp.get(route_key(hint))
    if hit is not None:
        return hit.strip()
    star = (mp.get("*") or "").strip()
    if star:
        return star
    return _catchall()


def _popen(cmd: str, raw: bytes) -> None:
    """Fire-and-forget. Same argv split as mill route. No shell."""
    from agent_coord.client.route_chain import popen_hint

    popen_hint(cmd, raw)


def spawn_hint(hint: dict[str, Any]) -> bool:
    """Start the mapped program. True if mill connect launched one."""
    cmd = program_for(hint)
    if not cmd:
        return False
    raw = json.dumps(hint, default=str, separators=(",", ":")).encode("utf-8")
    _popen(cmd, raw)
    return True


def spawn_cli(exe: str, extra: list[str], hint: dict[str, Any]) -> None:
    path = shutil.which(exe)
    if not path:
        raise NotImplementedError(f"{exe} not on PATH")
    subprocess.Popen(
        [path, *extra, spawn_prompt(hint)],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
