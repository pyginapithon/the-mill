"""human - one person, the bearer hash, and directory roles."""

from __future__ import annotations

from .db import call


def open(cn, digest: str) -> list[dict]:
    return call(cn, "mill_human_open", [digest])


def put(cn, digest: str, subject: str, role: str = "") -> list[dict]:
    rows = call(cn, "mill_human_put", [digest, subject or ""])
    hid = 0
    if rows:
        try:
            hid = int((rows[0] or {}).get("id") or 0)
        except (TypeError, ValueError):
            hid = 0
    if hid:
        call(cn, "mill_human_roles", [hid, role or ""])
    return rows
