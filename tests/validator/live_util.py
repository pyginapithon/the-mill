# -*- coding: utf-8 -*-
"""Shared live-probe helpers for tests/validator (importable; not a harness fork)."""
from __future__ import annotations

import ssl
from typing import Any


def p95(samples: list[float]) -> float:
    """Inclusive p95 for small N (loose SLO harness)."""
    if not samples:
        return 0.0
    xs = sorted(float(x) for x in samples)
    idx = min(len(xs) - 1, max(0, int(len(xs) * 0.95)))
    return xs[idx]


async def ws_connect_seated(
    url: str,
    token: str,
    ssl_ctx: ssl.SSLContext,
    *,
    open_timeout: float = 10.0,
) -> Any:
    """Open live wss with Bearer; return connected protocol (caller closes)."""
    import websockets

    hdrs = {"Authorization": "Bearer " + token}
    kw: dict[str, Any] = {"open_timeout": open_timeout, "ssl": ssl_ctx}
    try:
        kw["additional_headers"] = hdrs
        conn = websockets.connect(url, **kw)
    except TypeError:
        kw.pop("additional_headers", None)
        kw["extra_headers"] = hdrs
        conn = websockets.connect(url, **kw)
    ws = await conn.__aenter__()
    ws._mill_conn_cm = conn  # type: ignore[attr-defined]
    return ws


async def ws_close(ws: Any) -> None:
    cm = getattr(ws, "_mill_conn_cm", None)
    if cm is not None:
        await cm.__aexit__(None, None, None)
    else:
        await ws.close()


async def ws_rpc_rtt(
    ws: Any,
    *,
    command: str = "session",
    args: dict[str, Any] | None = None,
    timeout_s: float = 8.0,
) -> tuple[float, dict[str, Any]]:
    """Light JSON-RPC on the sitting /ws; return (rtt_s, reply)."""
    import asyncio
    import json
    import time
    import uuid

    req_id = "v-" + uuid.uuid4().hex[:12]
    body = {"id": req_id, "verb": command, "args": args if args is not None else {}}
    t0 = time.perf_counter()
    await ws.send(json.dumps(body))
    while True:
        raw = await asyncio.wait_for(ws.recv(), timeout=timeout_s)
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if not isinstance(msg, dict):
            continue
        if msg.get("id") != req_id:
            continue
        rtt = time.perf_counter() - t0
        return rtt, msg