# -*- coding: utf-8 -*-
"""#747: the ASGI wall caps a request body before it reads it.

An unauthenticated client could stream a huge body to /mill/v1/join (mill
command paths skip the Wall IP allow-list) and the wall read it whole into
memory before any check. A declared Content-Length over the cap is refused
with 413 before one body byte is read; a body with no length is read through
the stream with a running count and refused with 413 as soon as it passes
the cap. A request at the largest legitimate size still reaches the handler.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

from fastapi.testclient import TestClient

from agent_coord.lib.observe import parse_roots
from agent_coord.server import asgi
from agent_coord.server.asgi import make_asgi_app

HERE = Path(__file__).resolve().parents[2]
CAP = getattr(asgi, "BODY_MAX_BYTES", 256 * 1024)
CHUNK = 64 * 1024


def _app(monkeypatch):
    monkeypatch.setattr("agent_coord.server.admin.door.mode", lambda: "invite")
    return make_asgi_app(parse_roots(cwd=HERE), api_only=True)


def _scope(path: str, headers: list[tuple[bytes, bytes]]) -> dict:
    return {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "root_path": "",
        "headers": headers,
        "client": ("192.0.2.10", 40000),
        "server": ("127.0.0.1", 8765),
    }


def _drive(app, scope: dict, chunks: int) -> tuple[int, bytes, int]:
    """Run one request; return (status, body, body chunks the app pulled)."""
    pulled = [0]
    sent: list[dict] = []

    async def receive() -> dict:
        if pulled[0] >= chunks:
            return {"type": "http.disconnect"}
        pulled[0] += 1
        return {"type": "http.request", "body": b"x" * CHUNK, "more_body": pulled[0] < chunks}

    async def send(msg: dict) -> None:
        sent.append(msg)

    asyncio.run(app(scope, receive, send))
    start = next(m for m in sent if m["type"] == "http.response.start")
    body = b"".join(m.get("body", b"") for m in sent if m["type"] == "http.response.body")
    return int(start["status"]), body, pulled[0]


def test_declared_length_over_cap_is_413_before_any_read(monkeypatch) -> None:
    app = _app(monkeypatch)
    total = 64 * 1024 * 1024
    headers = [(b"content-type", b"application/json"), (b"content-length", str(total).encode())]
    for path in ("/mill/v1/join", "/api/mill/join"):
        status, body, pulled = _drive(app, _scope(path, headers), chunks=total // CHUNK)
        assert status == 413, (path, status, body[:200])
        assert pulled == 0, (path, pulled)
        assert b"413" in body or b"too large" in body


def test_streamed_body_without_length_stops_at_cap(monkeypatch) -> None:
    app = _app(monkeypatch)
    chunks = 64  # 4 MiB offered, no Content-Length (chunked)
    headers = [(b"content-type", b"application/json"), (b"transfer-encoding", b"chunked")]
    status, body, pulled = _drive(app, _scope("/mill/v1/join", headers), chunks=chunks)
    assert status == 413, (status, body[:200])
    assert pulled <= CAP // CHUNK + 1, pulled


def test_bad_content_length_is_400(monkeypatch) -> None:
    app = _app(monkeypatch)
    for bad in (b"abc", b"-5"):
        headers = [(b"content-length", bad)]
        status, _body, pulled = _drive(app, _scope("/mill/v1/join", headers), chunks=1)
        assert status == 400, (bad, status)
        assert pulled == 0


def test_largest_legitimate_body_still_reaches_the_handler(monkeypatch) -> None:
    """A todo with a 4096-character detail of astral characters, JSON-escaped
    the way the client sends it (12 bytes each), is well under the cap."""
    app = _app(monkeypatch)
    detail = "\U0001F600" * 4096
    payload = {"roster": "r", "need": "n" * 200, "detail": detail, "body": detail}
    raw = json.dumps(payload).encode("utf-8")
    assert len(raw) < CAP
    client = TestClient(app)
    r = client.post("/mill/v1/todo", content=raw, headers={"Content-Type": "application/json"})
    assert r.status_code != 413
    assert CAP >= 4 * len(json.dumps({"x": "\U0001F600" * 4096}))
