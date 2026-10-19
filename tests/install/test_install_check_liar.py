# -*- coding: utf-8 -*-
"""install-check-liar: good mill-wall office => mill install check ok:true.

JOB: install-check-liar
Probe HTTPS :443 with mill ca.crt (never wall.crt). :8765 down is not a Fail.
iOS meta in HTML, 720px in CSS. mill --agent launches Hidden UAC helper.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from agent_coord.install.host import (
    _wall_http,
    check_office,
    consume_mill_agent,
    ios_wall_contract,
    launch_hidden_scm_helper,
    mill_agent_mode,
    mill_ca_crt,
    share_wall_urls,
    wall_ui_default_dir,
)


class _Resp:
    def __init__(self, body: bytes, status: int = 200):
        self._body = body
        self.status = status

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_ios_contract_meta_in_html_720_in_css():
    html = (wall_ui_default_dir() / "board.html").read_text(encoding="utf-8")
    css = (wall_ui_default_dir() / "board.css").read_text(encoding="utf-8")
    assert ios_wall_contract(html, css) is True
    assert "max-width: 720px" not in html
    assert "max-width: 720px" in css
    assert 'name="viewport"' in html
    assert "apple-mobile-web-app" in html


def test_check_office_live_false_ios_ok(tmp_path: Path):
    from agent_coord.install import write_role

    write_role("wall", dest=tmp_path, http="nginx", apply=False)
    write_role("cloud", dest=tmp_path)
    probed = check_office(dest=tmp_path, live=False)
    ids = {c["id"]: c for c in probed["checks"]}
    assert ids["ios_wall_html"]["ok"] is True
    assert probed.get("ok") is True


def test_wall_http_https_up_ok_even_if_8765_would_fail(tmp_path: Path):
    ca = tmp_path / "ssl" / "ca.crt"
    ca.parent.mkdir()
    ca.write_text("mill-ca", encoding="utf-8")
    seen: list[str] = []

    def opener(url, timeout=5, context=None):
        seen.append(str(url))
        assert context is not None
        assert "8765" not in str(url)
        assert str(url).startswith("https://")
        if "/api/v1/agents" in str(url):
            return _Resp(json.dumps({"agents": []}).encode("utf-8"))
        return _Resp(b"<html>factory wall</html>")

    got = _wall_http(
        urls=["http://127.0.0.1:8765/", "https://192.0.2.10/"],
        ca=ca,
        urlopen=opener,
        ssl_context=object(),
    )
    assert got["ok"] is True
    assert "8765" not in got["detail"]
    assert all("8765" not in u for u in seen)
    assert any(u.startswith("https://") for u in seen)


def test_wall_http_floor_error_cannot_judge_here(tmp_path: Path):
    """html 200 + floor 500/timeout -> skip wall_not_session, not 'wall is in HERE'."""
    ca = tmp_path / "ssl" / "ca.crt"
    ca.parent.mkdir()
    ca.write_text("mill-ca", encoding="utf-8")

    def opener(url, timeout=5, context=None):
        if "/api/v1/agents" in str(url):
            raise TimeoutError("agents timeout")
        return _Resp(b"<html>factory wall</html>")

    got = _wall_http(
        urls=["https://192.0.2.10/"],
        ca=ca,
        urlopen=opener,
        ssl_context=object(),
    )
    assert got["ok"] is True
    assert got.get("floor_ok") is False
    assert got.get("not_session") is None


def test_wall_http_https_down_is_fail(tmp_path: Path):
    ca = tmp_path / "ssl" / "ca.crt"
    ca.parent.mkdir()
    ca.write_text("mill-ca", encoding="utf-8")

    def opener(url, timeout=5, context=None):
        raise OSError("connection refused")

    got = _wall_http(
        urls=["https://192.0.2.10/"],
        ca=ca,
        urlopen=opener,
        ssl_context=object(),
    )
    assert got["ok"] is False
    assert "8765" not in (got.get("detail") or "")


def test_wall_http_refuses_wall_crt(tmp_path: Path):
    leaf = tmp_path / "ssl" / "wall.crt"
    leaf.parent.mkdir()
    leaf.write_text("nope", encoding="utf-8")
    got = _wall_http(urls=["https://127.0.0.1/"], ca=leaf)
    assert got["ok"] is False
    assert "wall.crt" in got["detail"]


def test_wall_http_missing_ca_is_fail(tmp_path: Path):
    missing = tmp_path / "ssl" / "ca.crt"
    got = _wall_http(urls=["https://127.0.0.1/"], ca=missing)
    assert got["ok"] is False
    assert "ca.crt" in got["detail"]
    assert "wall.crt" in got["detail"]


def test_share_urls_are_https_not_8765():
    urls = share_wall_urls()
    assert urls
    assert all(u.startswith("https://") for u in urls)
    assert all(":8765" not in u for u in urls)


def test_mill_ca_name():
    p = mill_ca_crt(Path("C:/office"))
    assert p.name == "ca.crt"
    assert p.parent.name == "ssl"


def test_mill_agent_mode_env(monkeypatch):
    monkeypatch.delenv("MILL_AGENT", raising=False)
    assert mill_agent_mode() is False
    monkeypatch.setenv("MILL_AGENT", "1")
    assert mill_agent_mode() is True
    monkeypatch.delenv("MILL_AGENT", raising=False)
    assert mill_agent_mode(True) is True


def test_consume_mill_agent_sets_env(monkeypatch):
    monkeypatch.delenv("MILL_AGENT", raising=False)
    out = consume_mill_agent(["--agent", "install", "check"])
    assert out == ["install", "check"]
    assert os.environ.get("MILL_AGENT") == "1"
    monkeypatch.delenv("MILL_AGENT", raising=False)
    out = consume_mill_agent(["install", "check", "--agent"])
    assert out[0] == "install"
    assert os.environ.get("MILL_AGENT") != "1"


def test_launch_hidden_uac_helper_argv_hidden(tmp_path: Path):
    helper = tmp_path / "register-windows-services.ps1"
    helper.write_text("exit 0\n", encoding="utf-8")
    ran: list[list[str]] = []

    class Rec:
        returncode = 0
        stdout = ""
        stderr = ""

    def run_cmd(argv, capture_output=True, text=True):
        ran.append(list(argv))
        return Rec()

    notes = launch_hidden_scm_helper(helper, run_cmd=run_cmd, already_admin=False)
    assert notes == ["Hidden UAC helper (auto-exit)"]
    blob = " ".join(ran[0])
    assert "Hidden" in blob
    assert "RunAs" in blob or "Hidden" in ran[0]


def test_mill_install_help_has_agent():
    import contextlib
    import io

    import pytest

    from agent_coord.__main__ import main

    buf = io.StringIO()
    with pytest.raises(SystemExit):
        with contextlib.redirect_stdout(buf):
            main(["install", "--help"])
    text = buf.getvalue()
    assert "--agent" in text
    assert "MILL_AGENT" in text
