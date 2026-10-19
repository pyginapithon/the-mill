"""#399 mill-wall exposes pack version (header + GET)."""
from __future__ import annotations

from pathlib import Path

from agent_coord.install import packver
from agent_coord.server.middleware import make_handler


def test_package_version_info_from_checkout():
    info = packver.package_version_info()
    assert info["version"]
    assert info["source"] in ("pyproject", "dist", "local")
    assert packver.package_version() == info["version"]


def test_get_version_and_header(tmp_path, monkeypatch):
    # door open (non-invite)
    monkeypatch.setattr("agent_coord.server.admin.door.mode", lambda: "path")
    Handler = make_handler({}, api_only=True)

    class Fake:
        def __init__(self, path: str):
            self.path = path
            self.headers = {}
            self._code = None
            self._hdrs = {}
            self._body = b""
            self.wfile = self
            self.closed = False

        def write(self, b):
            self._body += b

        def send_response(self, code):
            self._code = code

        def send_header(self, k, v):
            self._hdrs[k.lower()] = v

        def end_headers(self):
            pass

        def log_message(self, *a):
            pass

    h = Fake("/mill/v1/version")
    # bind methods from Handler
    h.do_GET = Handler.do_GET.__get__(h, Fake)
    h._send = Handler._send.__get__(h, Fake)
    h._door_ok = Handler._door_ok.__get__(h, Fake)
    h._do_GET_inner = Handler._do_GET_inner.__get__(h, Fake)
    h.do_GET()
    assert h._code == 200
    assert h._hdrs.get("x-mill-version")
    assert h._hdrs.get("x-mill-api")
    import json

    body = json.loads(h._body.decode("utf-8"))
    assert body["version"] == h._hdrs["x-mill-version"]
    assert body["source"] in ("pyproject", "dist", "local")

    for path in ("/api/mill/version", "/api/version"):
        h2 = Fake(path)
        h2.do_GET = Handler.do_GET.__get__(h2, Fake)
        h2._send = Handler._send.__get__(h2, Fake)
        h2._door_ok = Handler._door_ok.__get__(h2, Fake)
        h2._do_GET_inner = Handler._do_GET_inner.__get__(h2, Fake)
        h2.do_GET()
        assert h2._code == 200, path
