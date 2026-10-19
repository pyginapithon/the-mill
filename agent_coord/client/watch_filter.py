# -*- coding: utf-8 -*-
"""Desk-local HINT allowlist for mill connect (not mill-wall).

Durable: ~/.mill/session/<desk>.want
  mail:MAIL =
  todo:TODO =
  * =

Empty file / no keys = accept all (current behavior).
Non-empty = only listed keys (specific beats; * accepts any).
PING never delivered as work anyway.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from agent_coord.client.route_chain import route_key
from agent_coord.helpers.ident import desk as slug_desk


def want_path(desk: str) -> Path:
    from agent_coord.client.offices import desk_local_file
    from agent_coord.config import mill_home

    hosted = desk_local_file(desk, "want")
    if hosted is not None:
        return hosted
    who = slug_desk(desk)
    dest = mill_home() / "session"
    dest.mkdir(parents=True, exist_ok=True)
    return dest / f"{who}.want"


def load_want(desk: str) -> dict[str, str]:
    p = want_path(desk)
    if not p.is_file():
        return {}
    out: dict[str, str] = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        key, raw = s.split("=", 1)
        key = key.strip()
        if key:
            out[key] = raw.strip()
    return out


def save_want(desk: str, want: dict[str, str]) -> Path:
    p = want_path(desk)
    lines = [
        "# HINT filter - route keys this desk acts on (empty map = all)",
        "# example: mail:MAIL =",
        "#          todo:TODO =",
        "#          * =",
        "",
    ]
    for key in sorted(want.keys(), key=lambda k: (k != "*", k)):
        lines.append(f"{key} = {want[key]}")
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


def wants(desk: str, msg: dict[str, Any]) -> bool:
    """True if drain should act on this HINT."""
    hint = str(msg.get("hint") or "")
    if hint == "PING":
        return False
    want = load_want(desk)
    if not want:
        return True
    key = route_key(msg)
    if key in want:
        return True
    if "*" in want:
        return True
    return False
