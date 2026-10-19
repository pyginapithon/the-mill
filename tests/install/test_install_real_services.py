# -*- coding: utf-8 -*-
"""OOTB real Windows SERVICES fail-closed + human warn (no live mill).

JOB: ootb-review-cuts (extends ootb-install-real-services)
SoR: share LAN/WAN URL; OS-branched HUMAN warn; packages!=services; loud Access Denied; wall_ps1 Ctrl+C stay-up.
"""
from __future__ import annotations

import io
import os
from pathlib import Path

import pytest

from agent_coord.install.host import (
    _apply_wall,
    _lan_sans,
    _make_wall_cert,
    _scm_needs_admin,
    _start_windows_service,
    _write_book,
    _write_wall,
    human_install_warn_lines,
    print_human_install_warn,
    print_loud_access_denied,
    share_wall_urls,
    wall_ps1,
    windows_scm_register_ps1,
    write_role,
    write_windows_scm_helper,
)


def test_human_warn_windows_short_clean():
    lines = human_install_warn_lines(nt=True, wsl=False)
    blob = "\n".join(lines).lower()
    assert len(lines) <= 5
    assert "127.0.0.1" in blob and "localhost" in blob
    assert "warning" in blob or "without a warning" in blob
    assert "advanced" in blob and "proceed" in blob
    assert "wall.crt" in blob and "import" in blob
    assert "other" in blob or "another" in blob or "device" in blob
    assert "mill" in blob
    assert "agent-coord alias" not in blob
    assert "wizard" not in blob
    assert "installer wizards" not in blob
    assert "wipe checklist" not in blob
    assert "winget uninstall" not in blob
    assert "share" in blob or "lan" in blob


def test_human_warn_linux_no_uac():
    lines = human_install_warn_lines(nt=False, wsl=False)
    blob = "\n".join(lines).lower()
    assert "uac" not in blob
    assert "winget" not in blob
    assert "schtasks" not in blob
    assert "systemd" in blob
    assert "sudo" in blob
    assert "proceed" in blob
    assert "wall.crt" in blob and "import" in blob
    assert "mill" in blob
    assert "agent-coord alias" not in blob


def test_human_warn_wsl_mentions_windows_mysql():
    lines = human_install_warn_lines(nt=False, wsl=True)
    blob = "\n".join(lines).lower()
    assert "uac" not in blob
    assert "3306" in blob
    assert "systemd" in blob or "sudo" in blob


def test_print_human_install_warn_writes_block():
    buf = io.StringIO()
    out = print_human_install_warn(stream=buf, nt=True, wsl=False)
    text = buf.getvalue()
    assert "HUMAN:" in text
    assert out and text.count("HUMAN:") >= 3


def test_write_role_server_dry_run_includes_human_warn(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        "agent_coord.install.preflight_server",
        lambda **kwargs: {
            "ok_apply": True,
            "verdict": "server-ready",
            "hints": [],
            "plan": {"dest": str(tmp_path)},
        },
    )
    buf = io.StringIO()
    monkeypatch.setattr("agent_coord.install.sys.stderr", buf)
    monkeypatch.setattr(
        "agent_coord.install.human_install_warn_lines",
        lambda **kwargs: human_install_warn_lines(nt=True, wsl=False),
    )
    row = write_role("server", dest=tmp_path / "o", dry_run=True)
    assert row.get("dry_run") is True
    assert row.get("mutated") is False
    assert row.get("human_warn")
    assert any("127.0.0.1" in w or "localhost" in w.lower() or "proceed" in w.lower() for w in row["human_warn"])
    assert "HUMAN:" in buf.getvalue()
    assert not (tmp_path / "o").exists() or not any((tmp_path / "o").iterdir())


@pytest.mark.parametrize(
    "msg,expect",
    [
        ("Access is denied.", True),
        ("Error 5: Access is denied", True),
        ("requires elevation", True),
        ("SERVICE_NAME: mill-wall\nSTATE: RUNNING", False),
        ("", False),
    ],
)
def test_scm_needs_admin(msg, expect):
    assert _scm_needs_admin(msg) is expect


def test_start_windows_service_denied_is_not_success(monkeypatch):
    def fake_run(cmd, capture_output=True, text=True):
        class R:
            returncode = 5
            stdout = ""
            stderr = "Access is denied."

        if list(cmd)[:2] == ["sc", "query"]:
            r = R()
            r.returncode = 0
            r.stdout = "SERVICE_NAME: MySQL80\nSTATE              : 1  STOPPED"
            return r
        return R()

    monkeypatch.setattr("agent_coord.install.subprocess.run", fake_run)
    buf = io.StringIO()
    monkeypatch.setattr("agent_coord.install.sys.stderr", buf)
    ok, note = _start_windows_service("MySQL80")
    assert ok is False
    assert "FAILED" in note
    assert "Admin/UAC" in note
    assert "console" in note.lower()
    assert "HUMAN:" in buf.getvalue() and "Access Denied" in buf.getvalue()


def test_start_windows_service_running_ok(monkeypatch):
    def fake_run(cmd, capture_output=True, text=True):
        class R:
            returncode = 0
            stdout = "SERVICE_NAME: MySQL80\nSTATE              : 4  RUNNING"
            stderr = ""

        return R()

    monkeypatch.setattr("agent_coord.install.subprocess.run", fake_run)
    ok, note = _start_windows_service("MySQL80")
    assert ok is True
    assert "RUNNING" in note


def test_write_book_apply_denied_scm_not_ok(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("agent_coord.install.os.name", "nt")
    monkeypatch.setattr(
        "agent_coord.install.host._book_services",
        lambda: [{"name": "MySQL80", "status": "Stopped", "start_type": "Automatic"}],
    )
    monkeypatch.setattr("agent_coord.install.host._book_reachable", lambda: {"ok": False, "error": "down"})
    monkeypatch.setattr(
        "agent_coord.install.host._start_windows_service",
        lambda name: (
            False,
            f"FAILED: {name} SCM start denied or failed (Admin/UAC required). "
            "Do not use mysqld --console as Pass.",
        ),
    )
    row = _write_book(tmp_path, apply=True, bind="127.0.0.1")
    assert row.get("ok") is False
    warn_applied = list(row.get("warnings") or []) + list(row.get("applied") or [])
    assert any("FAILED" in w and "Admin/UAC" in w for w in warn_applied)
    assert any("mysqld --console" in w.lower() for w in warn_applied)


def test_share_wall_urls_leads_with_lan_not_localhost():
    urls = share_wall_urls(public_bind="127.0.0.1", private_ips=["198.51.100.42", "198.51.100.43"])
    assert urls[0] == "https://198.51.100.42/"
    assert urls[0] != "https://127.0.0.1/"
    assert "https://127.0.0.1/" in urls


def test_share_wall_urls_wan_bind_leads():
    urls = share_wall_urls(public_bind="203.0.113.10", public=True, private_ips=["198.51.100.42"])
    assert urls[0] == "https://203.0.113.10/"


def test_share_wall_urls_explicit_lan_bind():
    urls = share_wall_urls(public_bind="198.51.100.1", private_ips=["198.51.100.42"])
    assert urls[0] == "https://198.51.100.1/"


@pytest.mark.skipif(os.name != "nt", reason="Windows SCM/pathlib only")
def test_write_wall_next_steps_share_url_and_no_import(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("agent_coord.install.os.name", "nt")
    monkeypatch.setattr("agent_coord.install.python_exe", lambda: "python")
    monkeypatch.setattr("agent_coord.install.host._repo_cwd", lambda: tmp_path)
    monkeypatch.setattr("agent_coord.install.deploy_www", lambda dest: dest / "www")
    monkeypatch.setattr("agent_coord.install.host._httpd_bins", lambda: {})
    monkeypatch.setattr(
        "agent_coord.install.host.share_wall_urls",
        lambda **kwargs: ["https://198.51.100.7/", "https://127.0.0.1/"],
    )
    monkeypatch.setattr("agent_coord.install.write_windows_scm_helper", lambda dest: dest / "register-windows-services.ps1")
    # avoid real netbind cert mkdir issues
    monkeypatch.setattr(
        "agent_coord.server.netbind.cert_paths",
        lambda dest=None: {"cert": "c", "key": "k", "ssl_dir": "s", "cert_exists": False},
    )
    monkeypatch.setattr(
        "agent_coord.server.netbind.resolve_listen_hosts",
        lambda **kwargs: ["127.0.0.1", "198.51.100.7"],
    )
    # nginx-wall.conf needs static_dir
    monkeypatch.setattr("agent_coord.install.static_dir", lambda: tmp_path / "web" / "static")
    (tmp_path / "web" / "static").mkdir(parents=True, exist_ok=True)
    (tmp_path / "www").mkdir(exist_ok=True)

    dest = tmp_path / "office"
    dest.mkdir()
    # write_windows_scm_helper real for coverage
    monkeypatch.setattr(
        "agent_coord.install.write_windows_scm_helper",
        write_windows_scm_helper,
    )
    row = _write_wall(
        dest,
        http="nginx",
        apply=False,
        public_bind="127.0.0.1",
        public_port=443,
        lan_only=True,
    )
    assert row["url"] == "https://198.51.100.7/"
    nxt = "\n".join(row["next"])
    assert nxt.index("https://198.51.100.7/") < nxt.index("127.0.0.1")
    assert "Do not import wall.crt" in nxt
    assert "127.0.0.1" in nxt and "localhost" in nxt
    assert ("hidden" in nxt.lower()) or ("elevate" in nxt.lower()) or ("packages" in nxt.lower() and "service" in nxt.lower())
    assert (dest / "register-windows-services.ps1").is_file()
    helper = (dest / "register-windows-services.ps1").read_text(encoding="utf-8")
    assert "packages" in helper.lower() or "SERVICES" in helper
    assert "mill-wall" in helper.lower()


def test_wall_ps1_ctrl_c_stay_up(tmp_path: Path):
    body = wall_ps1(
        python="python",
        bind="127.0.0.1",
        port=18765,
        cwd=tmp_path,
        log=tmp_path / "wall.log",
        api_only=True,
    )
    assert "TreatControlCAsInput" in body
    assert "CancelKeyPress" in body
    assert "0xC000013A" in body or "3221225786" in body or "CtrlC" in body
    assert "while ($true)" in body


def test_loud_access_denied_prints_human():
    buf = io.StringIO()
    print_loud_access_denied("mill-wall: Access is denied.", stream=buf)
    assert "HUMAN:" in buf.getvalue()
    assert "Access Denied" in buf.getvalue()


def test_windows_scm_helper_text_mentions_elevated_services():
    text = windows_scm_register_ps1().lower()
    assert "admin" in text or "uac" in text or "elevat" in text
    assert "service" in text
    assert "mysqld" in text or "mysql" in text
    assert "mill-wall" in text or "access denied" in text.lower()


def test_scm_helper_hidden_auto_exit():
    body = windows_scm_register_ps1()
    assert "exit 0" in body
    assert "pause" not in body.lower()
    assert "read-host" not in body.lower()
    assert "WindowStyle Hidden" in body or "auto-exit" in body.lower() or "Hidden" in body

def _find_openssl():
    import shutil

    for c in (Path(shutil.which("openssl") or ""),):
        if c.is_file():
            return c
    return None


def test_make_wall_cert_ca_signed_leaf_san(tmp_path: Path, monkeypatch):
    import os
    import subprocess

    openssl = _find_openssl()
    if openssl is None:
        pytest.skip("openssl not available")
    monkeypatch.setattr(
        "agent_coord.install.host._trust_mill_ca_current_user",
        lambda ca_crt: ["trust mocked"],
    )
    ssl_dir = tmp_path / "ssl"
    crt, key = _make_wall_cert(ssl_dir, openssl)
    assert crt.is_file() and key.is_file()
    ca = ssl_dir / "ca.crt"
    assert ca.is_file() and (ssl_dir / "ca.key").is_file()
    env = os.environ.copy()
    cnf = openssl.parent.parent / "conf" / "openssl.cnf"
    if cnf.is_file():
        env["OPENSSL_CONF"] = str(cnf)
    ver = subprocess.run(
        [str(openssl), "verify", "-CAfile", str(ca), str(crt)],
        capture_output=True,
        text=True,
        env=env,
    )
    assert ver.returncode == 0 and "OK" in ((ver.stdout or "") + (ver.stderr or ""))
    text = subprocess.run(
        [str(openssl), "x509", "-in", str(crt), "-noout", "-text"],
        capture_output=True,
        text=True,
        env=env,
    )
    blob = (text.stdout or "") + (text.stderr or "")
    assert "localhost" in blob
    assert "127.0.0.1" in blob
    issuer = subprocess.run(
        [str(openssl), "x509", "-in", str(crt), "-noout", "-issuer"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert "mill-wall-ca" in (issuer.stdout or "")
    mtime = crt.stat().st_mtime
    crt2, _key2 = _make_wall_cert(ssl_dir, openssl)
    assert crt2 == crt
    assert crt.stat().st_mtime == mtime


def test_apply_wall_mints_ca_and_leaf(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("agent_coord.install.host.os.name", "posix")
    monkeypatch.setattr(
        "agent_coord.install.host.shutil.which",
        lambda name: "/usr/bin/openssl" if name == "openssl" else None,
    )
    seen: dict[str, Path] = {}

    def fake(ssl_dir: Path, openssl: Path):
        seen["ssl"] = ssl_dir
        seen["openssl"] = openssl
        return ssl_dir / "wall.crt", ssl_dir / "wall.key"

    monkeypatch.setattr("agent_coord.install.host._make_wall_cert", fake)
    done = _apply_wall(
        {"systemd": tmp_path / "mill-wall.service"},
        http="service",
        httpd={},
        dest=tmp_path,
    )
    steps = done["steps"] if isinstance(done, dict) else done
    assert done.get("ok") is True if isinstance(done, dict) else True
    assert seen["ssl"] == tmp_path / "ssl"
    assert seen["openssl"] == Path("/usr/bin/openssl")
    assert any("wall.crt" in line and "ca.crt" in line for line in steps)


def test_apply_wall_reports_missing_openssl(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("agent_coord.install.host.os.name", "posix")
    monkeypatch.setattr("agent_coord.install.host.shutil.which", lambda _name: None)
    done = _apply_wall(
        {"systemd": tmp_path / "mill-wall.service"},
        http="service",
        httpd={},
        dest=tmp_path,
    )
    steps = done["steps"] if isinstance(done, dict) else done
    assert isinstance(done, dict)
    assert done.get("ok") is False
    assert done.get("failed_step") == "openssl"
    assert any(line.startswith("FAILED:") and "openssl" in line for line in steps)


def test_lan_sans_includes_public_address(monkeypatch):
    monkeypatch.setenv("AGENT_COORD_WALL_IPS", "203.0.113.10, wall.example")
    blob = _lan_sans()
    assert "IP:203.0.113.10" in blob
    assert "DNS:wall.example" in blob
    assert "DNS:localhost" in blob

