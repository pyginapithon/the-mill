# -*- coding: utf-8 -*-
"""#654: the client never follows a redirect while it carries a credential."""
from __future__ import annotations

import http.server
import threading
from pathlib import Path

import pytest

from agent_coord.helpers.errors import CoordError

CODES = (301, 302, 303, 307, 308)


class _Seen:
    def __init__(self) -> None:
        self.first: list[str] = []
        self.second: list[dict] = []


def _servers(code: int):
    seen = _Seen()

    class Second(http.server.BaseHTTPRequestHandler):
        def _hit(self) -> None:
            seen.second.append(
                {
                    "path": self.path,
                    "auth": self.headers.get("Authorization"),
                    "invite": self.headers.get("X-Mill-Invite"),
                }
            )
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok": true}')

        do_GET = do_POST = _hit

        def log_message(self, *a):  # quiet
            pass

    second = http.server.HTTPServer(("127.0.0.1", 0), Second)
    port2 = second.server_address[1]

    class First(http.server.BaseHTTPRequestHandler):
        def _hit(self) -> None:
            seen.first.append(self.path)
            self.send_response(code)
            self.send_header("Location", f"http://127.0.0.1:{port2}{self.path}")
            self.send_header("Content-Length", "0")
            self.end_headers()

        do_GET = do_POST = _hit

        def log_message(self, *a):
            pass

    first = http.server.HTTPServer(("127.0.0.1", 0), First)
    for s in (first, second):
        threading.Thread(target=s.serve_forever, daemon=True).start()
    return first, second, seen


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    return tmp_path


@pytest.mark.parametrize("code", CODES)
def test_join_redirect_is_refused_and_second_url_gets_nothing(home, monkeypatch, code):
    from agent_coord.client import http as h

    first, second, seen = _servers(code)
    try:
        monkeypatch.setattr(h, "mill_url", lambda: f"http://127.0.0.1:{first.server_address[1]}")
        with pytest.raises(CoordError) as ei:
            h.mill_http_call({"verb": "join", "owner": "cold", "token": "seat-placeholder"})
        assert str(code) in str(ei.value)
        assert "redirect refused" in str(ei.value)
        assert seen.first, "the named wall got the call"
        assert seen.second == []
    finally:
        first.shutdown()
        second.shutdown()


@pytest.mark.parametrize("code", CODES)
def test_ca_fetch_redirect_sends_no_invite_to_second_url(home, code):
    from agent_coord.client import http as h

    first, second, seen = _servers(code)
    try:
        got = h.fetch_mill_ca(
            f"http://127.0.0.1:{first.server_address[1]}",
            dest=Path(home) / "ca.crt",
            invite="invite-placeholder",
        )
        assert got is None
        assert not (Path(home) / "ca.crt").exists()
        assert seen.first == ["/api/ca.crt", "/ca.crt"]
        assert seen.second == []
    finally:
        first.shutdown()
        second.shutdown()


def test_wake_and_client_share_one_opener():
    from agent_coord.client import http as h
    from agent_coord.helpers import nofollow
    from agent_coord.server import wake

    import inspect

    assert "open_no_redirect" in inspect.getsource(wake._open)
    assert "open_no_redirect" in inspect.getsource(h._open)
    assert nofollow.NoRedirect().redirect_request(None, None, 308, "", {}, "http://x/") is None
