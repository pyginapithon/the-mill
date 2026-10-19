"""Local mill grok-bot doorbell. mill connect POSTs HINT JSON here.

Bind from AGENT_COORD_BOT_WAKE_URL (loopback HTTP only). Default:

  http://127.0.0.1:18791/wake

  $env:AGENT_COORD_BOT_WAKE_URL = "http://127.0.0.1:18791/wake"
  python tools/bot_wake_listen.py
  mill connect --owner DESK --vendor grok-bot
"""
from __future__ import annotations

import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

DEFAULT_URL = "http://127.0.0.1:18791/wake"
LOOPBACK = {"127.0.0.1", "localhost", "::1"}


def wake_url() -> str:
    raw = (os.environ.get("AGENT_COORD_BOT_WAKE_URL") or "").strip()
    if raw:
        return raw
    if len(sys.argv) > 1 and sys.argv[1].strip():
        return sys.argv[1].strip()
    return DEFAULT_URL


def parse_bind(url: str) -> tuple[str, int, str]:
    u = urlparse((url or "").strip())
    if u.scheme != "http":
        raise SystemExit(f"bot-wake-listen: only http:// loopback, got {url!r}")
    host = (u.hostname or "").strip().lower()
    if host not in LOOPBACK:
        raise SystemExit(f"bot-wake-listen: refuse non-loopback host {host!r}")
    bind = "127.0.0.1" if host != "::1" else "::1"
    port = int(u.port or 80)
    path = u.path or "/"
    if not path.startswith("/"):
        path = "/" + path
    return bind, port, path.rstrip("/") or "/"


def _log_path() -> Path:
    try:
        from agent_coord.config import mill_home

        dest = mill_home() / "session"
    except Exception:
        dest = Path.home() / ".mill" / "session"
    dest.mkdir(parents=True, exist_ok=True)
    return dest / "bot-wake-listen.jsonl"


class Wake(BaseHTTPRequestHandler):
    path_ok = "/wake"
    log_file: Path | None = None

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("wake-listen " + (fmt % args) + "\n")

    def _route_ok(self) -> bool:
        return self.path.split("?", 1)[0] == self.path_ok

    def do_POST(self) -> None:
        if not self._route_ok():
            self.send_error(404)
            return
        n = int(self.headers.get("Content-Length") or "0")
        raw = self.rfile.read(n) if n else b"{}"
        try:
            body = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            body = {"raw": raw.decode("utf-8", "replace")[:200]}
        line = json.dumps(body, default=str)
        print("WAKE", line, flush=True)
        if self.log_file is not None:
            with self.log_file.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        self.send_response(204)
        self.end_headers()
        if isinstance(body, dict):
            owner = (os.environ.get("AGENT_COORD_OWNER") or "").strip()

            def _run() -> None:
                try:
                    from agent_coord.client.wake_post import accept_wake

                    accept_wake(body, owner)
                except Exception:
                    return

            threading.Thread(target=_run, name="mill-wake-post", daemon=True).start()

    def do_GET(self) -> None:
        if not self._route_ok():
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"mill bot-wake-listen ok\n")


def main() -> int:
    url = wake_url()
    host, port, path = parse_bind(url)
    Wake.path_ok = path
    Wake.log_file = _log_path()
    httpd = ThreadingHTTPServer((host, port), Wake)
    print(f"listening {url}", flush=True)
    print(f"log {Wake.log_file}", flush=True)
    httpd.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
