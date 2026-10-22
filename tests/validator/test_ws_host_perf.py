# -*- coding: utf-8 -*-
"""Live /ws host perf: sit latency, light RPC RTT, reconnect (mill_live).

Reuses client helpers (mill_ws_url) and websockets patterns from the product
client - live wss, not fakes. LOOSE thresholds first; measured values go in
assert messages for tightening later.
"""
from __future__ import annotations

import asyncio
import ssl
import sys
import time
from pathlib import Path
from typing import Any

import httpx
import pytest

_VDIR = Path(__file__).resolve().parent
if str(_VDIR) not in sys.path:
    sys.path.insert(0, str(_VDIR))

from live_util import p95, ws_close, ws_connect_seated, ws_rpc_rtt  # noqa: E402

pytestmark = pytest.mark.mill_live

# Loose SLOs (first pass). Tighten once measured numbers stabilize.
_SIT_P95_S = 2.0
_RPC_P95_S = 2.0
_RECONNECT_S = 5.0
_SIT_SAMPLES = 5
_RPC_SAMPLES = 8


def _run(coro):
    return asyncio.run(coro)


def test_ws_connect_seated_p95(
    mill_ws_url_live: str,
    require_live_creds: tuple[str, str],
    mill_ssl_context: ssl.SSLContext,
) -> None:
    _desk, token = require_live_creds
    url = mill_ws_url_live

    async def once() -> float:
        t0 = time.perf_counter()
        ws = await ws_connect_seated(url, token, mill_ssl_context)
        try:
            # Seated = auth passed and socket usable (server closes 4401 on bad token).
            sit_s = time.perf_counter() - t0
            rtt, reply = await ws_rpc_rtt(ws, command="session", args={})
            assert reply.get("ok") is True or "error" in reply, (
                f"post-sit rpc unexpected: {reply!r} sit_s={sit_s:.3f} rtt={rtt:.3f}"
            )
            return sit_s
        finally:
            await ws_close(ws)

    samples: list[float] = []
    for _ in range(_SIT_SAMPLES):
        samples.append(_run(once()))
        time.sleep(0.15)

    got = p95(samples)
    assert got < _SIT_P95_S, (
        f"connect->seated p95={got:.3f}s samples={[round(s, 3) for s in samples]} "
        f"(loose SLO <{_SIT_P95_S}s)"
    )


def test_ws_light_rpc_rtt_p95(
    mill_ws_url_live: str,
    require_live_creds: tuple[str, str],
    mill_ssl_context: ssl.SSLContext,
) -> None:
    _desk, token = require_live_creds
    url = mill_ws_url_live

    async def go() -> list[float]:
        ws = await ws_connect_seated(url, token, mill_ssl_context)
        try:
            rtts: list[float] = []
            for _ in range(_RPC_SAMPLES):
                rtt, reply = await ws_rpc_rtt(ws, command="session", args={})
                assert isinstance(reply, dict), f"rpc reply not dict: {reply!r}"
                assert reply.get("ok") is True or "result" in reply or "error" in reply, (
                    f"rpc shape: {reply!r} rtt={rtt:.3f}s"
                )
                rtts.append(rtt)
            return rtts
        finally:
            await ws_close(ws)

    samples = _run(go())
    got = p95(samples)
    assert got < _RPC_P95_S, (
        f"light RPC RTT p95={got:.3f}s samples={[round(s, 3) for s in samples]} "
        f"(loose SLO <{_RPC_P95_S}s)"
    )


def test_ws_reconnect_resit_bound(
    mill_ws_url_live: str,
    require_live_creds: tuple[str, str],
    mill_ssl_context: ssl.SSLContext,
) -> None:
    _desk, token = require_live_creds
    url = mill_ws_url_live

    async def go() -> float:
        ws = await ws_connect_seated(url, token, mill_ssl_context)
        await ws_close(ws)
        t0 = time.perf_counter()
        ws2 = await ws_connect_seated(url, token, mill_ssl_context)
        try:
            rtt, reply = await ws_rpc_rtt(ws2, command="session", args={})
            elapsed = time.perf_counter() - t0
            assert reply.get("ok") is True or "error" in reply, (
                f"re-sit rpc unexpected: {reply!r} reconnect_s={elapsed:.3f} rtt={rtt:.3f}"
            )
            return elapsed
        finally:
            await ws_close(ws2)

    elapsed = _run(go())
    assert elapsed < _RECONNECT_S, (
        f"drop+re-sit bound={elapsed:.3f}s (loose SLO <{_RECONNECT_S}s)"
    )


def test_ws_rpc_under_concurrent_http(
    mill_ws_url_live: str,
    require_live_creds: tuple[str, str],
    mill_ssl_context: ssl.SSLContext,
    mill_base_url: str,
    mill_tls_verify: Any,
) -> None:
    """Optional lighter: concurrent HTTP v1 while one /ws sit - RPC still under loose SLO."""
    _desk, token = require_live_creds
    url = mill_ws_url_live

    async def go() -> list[float]:
        ws = await ws_connect_seated(url, token, mill_ssl_context)
        try:
            def _http_burst() -> None:
                with httpx.Client(verify=mill_tls_verify, timeout=15.0) as c:
                    for path in (
                        "/api/v1/agents?project=Office&limit=50",
                        "/api/v1/scores?project=Office&limit=20",
                        "/api/v1/holds?project=Office&limit=20",
                    ):
                        r = c.get(mill_base_url + path)
                        assert r.status_code == 200, f"{path} -> {r.status_code}"

            import concurrent.futures

            rtts: list[float] = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                fut = pool.submit(_http_burst)
                for _ in range(5):
                    rtt, reply = await ws_rpc_rtt(ws, command="session", args={})
                    assert reply.get("ok") is True or "error" in reply, reply
                    rtts.append(rtt)
                fut.result(timeout=60)
            return rtts
        finally:
            await ws_close(ws)

    samples = _run(go())
    got = p95(samples)
    assert got < _RPC_P95_S, (
        f"RPC under concurrent HTTP p95={got:.3f}s "
        f"samples={[round(s, 3) for s in samples]} (loose SLO <{_RPC_P95_S}s)"
    )