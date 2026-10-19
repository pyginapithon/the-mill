# -*- coding: utf-8 -*-
"""Benchmark mill-wall request time (instrumented duration_ms). Not a Wall API dump."""
from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from agent_coord.lib.observe import parse_roots
from agent_coord.server.asgi import latency_snapshot, make_asgi_app


def test_howto_latency_p95() -> None:
    here = Path(__file__).resolve().parents[2]
    app = make_asgi_app(parse_roots(cwd=here), api_only=False)
    client = TestClient(app)
    client.get("/api/howto")
    n = 20
    for _ in range(n):
        r = client.get("/api/howto")
        assert r.status_code == 200
        ms = float(r.headers.get("x-mill-duration-ms") or "0")
        assert ms >= 0
    snap = latency_snapshot()
    assert snap["n"] >= n
    # Loose CI bound: catch accidental multi-second Handler path, not a load test.
    assert float(snap["p95_ms"]) < 2000.0
    assert float(snap["max_ms"]) < 5000.0
