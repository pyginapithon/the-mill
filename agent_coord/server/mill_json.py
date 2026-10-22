# -*- coding: utf-8 -*-
"""Stamp mill version on every top-level JSON object the wall emits.

Single source: agent_coord.install.packver.package_version (pyproject / dist).
Field name is always ``mill`` (string). Lean command payloads inside ``result``
stay untouched - version lives on the envelope only.

Bare JSON arrays (rare; desk commands are /ws RPC) wrap as
``{"result": [...], "mill": "<ver>"}`` so the wire can carry the version
without inventing a second field name. CLI desk commands print the full
ok/mill/id/result/sync envelope by default (``mill --raw`` unwraps);
join HTTP is already an object.
"""
from __future__ import annotations

import json
from typing import Any


def mill_version() -> str:
    """Resolved pack version (checkout pyproject, else installed dist, else 0+local)."""
    from agent_coord.install.packver import package_version

    return package_version()


def stamp_mill(obj: Any) -> Any:
    """Attach ``mill`` to a top-level JSON value.

    - dict: copy + ``mill`` (does not deep-rewrite nested rows)
    - list: wrap ``{"result": list, "mill": ver}`` so the frame can carry version
    - other: returned unchanged (callers should emit objects)
    """
    ver = mill_version()
    if isinstance(obj, dict):
        out = dict(obj)
        out["mill"] = ver
        return out
    if isinstance(obj, list):
        return {"result": obj, "mill": ver}
    return obj


def dumps_mill(obj: Any, **kwargs: Any) -> str:
    """json.dumps after stamp_mill. default=str unless caller overrides."""
    kwargs.setdefault("default", str)
    return json.dumps(stamp_mill(obj), **kwargs)


def dumps_mill_bytes(obj: Any, **kwargs: Any) -> bytes:
    return dumps_mill(obj, **kwargs).encode("utf-8")


def with_bytes(reply: dict) -> tuple[dict, int]:
    """#288: the reply carries its own size as ``bytes`` (json.dumps default separators).

    One dump of the reply without the field; the field adds ``, "bytes": N`` before
    the closing brace, so the total is solved from the digit count, no second dump.
    """
    base = len(json.dumps(reply, default=str).encode("utf-8"))
    extra = len(', "bytes": ') if reply else len('"bytes": ')
    n = base + extra + 1
    while base + extra + len(str(n)) != n:
        n = base + extra + len(str(n))
    out = dict(reply)
    out["bytes"] = n
    return out, n
