# -*- coding: utf-8 -*-
"""Same client tools against a localhost mill (open door) and a cloud mill (invite door)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from agent_coord.client.offices import bind_cli_office, read_office_invite, write_alias, write_host_invite, write_host_url
from agent_coord.lib.observe import parse_roots
from agent_coord.client.http import mill_http_call
from agent_coord.server.asgi import make_asgi_app

_CA = b"-----BEGIN CERTIFICATE-----\nMIIB\n-----END CERTIFICATE-----\n"
_INVITE = "cloud-key"


def _wall(monkeypatch, door: str):
    monkeypatch.setattr("agent_coord.server.admin.door.mode", lambda: door)
    monkeypatch.setattr("agent_coord.server.admin.door.check", lambda token: door != "invite" or token == _INVITE)
    monkeypatch.setattr("agent_coord.server.admin.door.match_key", lambda token: None)
    here = Path(__file__).resolve().parents[2]
    app = make_asgi_app(parse_roots(cwd=here), api_only=False)
    return TestClient(app)


def _patch_ca(monkeypatch, tmp_path: Path) -> None:
    cert = tmp_path / "ca.crt"
    cert.write_bytes(_CA)
    monkeypatch.setattr("agent_coord.install.host.mill_ca_crt", lambda dest=None: cert)
    monkeypatch.setattr("agent_coord.install.mill_ca_crt", lambda dest=None: cert)


def test_localhost_ca_is_open(monkeypatch, tmp_path: Path) -> None:
    _patch_ca(monkeypatch, tmp_path)
    client = _wall(monkeypatch, "path")
    got = client.get("/ca.crt")
    assert got.status_code == 200
    assert b"BEGIN CERTIFICATE" in got.content


def test_cloud_ca_needs_invite(monkeypatch, tmp_path: Path) -> None:
    _patch_ca(monkeypatch, tmp_path)
    client = _wall(monkeypatch, "invite")
    closed = client.get("/ca.crt")
    assert closed.status_code == 404
    opened = client.get("/api/ca.crt", headers={"X-Mill-Invite": _INVITE})
    assert opened.status_code == 200
    assert b"BEGIN CERTIFICATE" in opened.content


def test_register_sends_saved_cloud_invite(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    bind_cli_office("cloud-mill")
    try:
        write_alias("cloud-mill", "203.0.113.10", dest=tmp_path)
        write_host_url("203.0.113.10", "https://203.0.113.10", dest=tmp_path)
        write_host_invite("203.0.113.10", _INVITE, dest=tmp_path)
        assert read_office_invite(dest=tmp_path) == _INVITE
        seen: dict[str, str] = {}

        class Resp:
            def read(self):
                return json.dumps({"ok": True, "owner": "build-cloud", "desk_id": 1}).encode()

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        def fake_urlopen(req, context=None, timeout=None):
            seen["invite"] = req.get_header("X-mill-invite") or ""
            seen["url"] = req.full_url
            return Resp()

        monkeypatch.setattr("agent_coord.client.http.urllib.request.urlopen", fake_urlopen)
        row = mill_http_call({"verb": "join", "project": "the-mill", "owner": "build-cloud", "doing": "present"})
        assert row.get("ok") is True
        assert seen["invite"] == _INVITE
        assert seen["url"].startswith("https://203.0.113.10/mill/v1/join")
    finally:
        bind_cli_office("")


@pytest.mark.parametrize("door_mode", ["invite", "directory"])
def test_cloud_ca_accepts_seat_only(monkeypatch, tmp_path: Path, door_mode: str) -> None:
    """A join seat opens GET /api/ca.crt only. It is not a door invite."""
    from agent_coord.client.tokens import token_hash

    _patch_ca(monkeypatch, tmp_path)
    monkeypatch.setattr("agent_coord.server.admin.door.mode", lambda: door_mode)
    monkeypatch.setattr("agent_coord.server.admin.door.check", lambda token: False)
    monkeypatch.setattr("agent_coord.server.admin.door.match_key", lambda token: None)
    seat = "seat-plain-token"
    digest = token_hash(seat)

    class Cur:
        def __init__(self) -> None:
            self.row = None

        def execute(self, sql, args):
            self.row = (digest,) if args and args[0] == digest else None

        def fetchone(self):
            return self.row

        def close(self):
            return None

    class Cn:
        def cursor(self, *args, **kwargs):
            return Cur()

        def close(self):
            return None

    monkeypatch.setattr("agent_coord.server.admin.door._db", lambda: Cn())
    here = Path(__file__).resolve().parents[2]
    client = TestClient(make_asgi_app(parse_roots(cwd=here), api_only=False))
    opened = client.get("/api/ca.crt", headers={"X-Mill-Invite": seat})
    assert opened.status_code == 200
    assert b"BEGIN CERTIFICATE" in opened.content
    other = client.get("/api/version", headers={"X-Mill-Invite": seat})
    assert other.status_code == 404
    assert b"not found" in other.content
    bad = client.get("/api/ca.crt", headers={"X-Mill-Invite": "not-a-seat"})
    assert bad.status_code == 404
    assert b"not found" in bad.content
    missing = tmp_path / "gone.crt"
    monkeypatch.setattr("agent_coord.install.mill_ca_crt", lambda dest=None: missing)
    gone = client.get("/api/ca.crt", headers={"X-Mill-Invite": seat})
    assert gone.status_code == 404
    assert gone.content == b"no mill ca\n"
