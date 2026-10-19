# -*- coding: utf-8 -*-
"""OOTB empty-machine bootstrap + ensure-deps (no live mill / no --apply).

JOB: ootb-empty-bootstrap
"""
from __future__ import annotations

from pathlib import Path

import pytest

from agent_coord.install import (
    WINGET_MYSQL_ID,
    WINGET_PYTHON_ID,
    WINGET_SILENT,
    apt_install_argv,
    ensure_deps,
    ensure_deps_plan,
    human_install_warn_lines,
    probe_deps,
    winget_install_argv,
    write_role,
)


def test_winget_install_argv_is_silent_no_wizard():
    for pkg in (WINGET_PYTHON_ID, WINGET_MYSQL_ID):
        cmd = winget_install_argv(pkg)
        blob = " ".join(cmd).lower()
        assert "--disable-interactivity" in cmd
        assert "--accept-package-agreements" in cmd
        assert "--accept-source-agreements" in cmd
        assert "wizard" not in blob
        assert "configurator" not in blob
        assert cmd[:5] == ["winget", "install", "--id", pkg, "-e"]
    mysql = " ".join(winget_install_argv(WINGET_MYSQL_ID))
    assert "--override" in mysql and "/quiet" in mysql
    assert "--disable-interactivity" in WINGET_SILENT


def test_apt_install_argv_noninteractive():
    cmd = apt_install_argv("nginx", "mysql-community-server")
    assert cmd[:4] == ["sudo", "apt-get", "install", "-y"]
    assert "nginx" in cmd and "mysql-community-server" in cmd
    assert "uac" not in " ".join(cmd).lower()
    assert "winget" not in " ".join(cmd).lower()


def test_ensure_deps_plan_reuses_healthy_installs_only_missing():
    probe = {
        "platform": {"nt": True, "wsl": False, "os": "windows"},
        "python": {"ok": True, "version": [3, 12, 0]},
        "mill": {"ok": True, "path": "mill"},
        "mysql": {"ok": False, "service": "MySQL84", "state": "ABSENT"},
        "dest": {"already": False, "dest": "C:/tmp/.mill"},
        "wall": {"ok": False},
        "missing": ["mysql"],
        "reuse": ["python", "mill"],
    }
    plan = ensure_deps_plan(probe=probe, nt=True, wsl=False)
    actions = {(a["piece"], a["action"]) for a in plan["actions"]}
    assert ("python", "reuse") in actions
    assert ("mill", "reuse") in actions
    assert ("mysql", "install") in actions
    assert plan.get("wizard") is False
    assert plan.get("silent") is True
    flat = [" ".join(c) for c in plan["cmds"]]
    assert any("Oracle.MySQL" in x and "--disable-interactivity" in x for x in flat)
    assert all("Lounge" not in x for x in flat)


def test_ensure_deps_plan_linux_no_winget_no_uac():
    probe = {
        "platform": {"nt": False, "wsl": False, "os": "linux"},
        "python": {"ok": True},
        "mill": {"ok": True},
        "mysql": {"ok": False},
        "dest": {"already": False},
        "wall": {"ok": False},
        "missing": ["mysql"],
        "reuse": ["python", "mill"],
    }
    plan = ensure_deps_plan(probe=probe, nt=False, wsl=False)
    blob = " ".join(" ".join(c) for c in plan["cmds"]).lower()
    assert "winget" not in blob
    assert "uac" not in blob
    assert "apt-get" in blob and "-y" in blob
    assert "systemctl" in blob


def test_ensure_deps_plan_wsl_no_hijack_mysql():
    probe = {
        "platform": {"nt": False, "wsl": True, "os": "wsl"},
        "python": {"ok": True},
        "mill": {"ok": True},
        "mysql": {"ok": False},
        "dest": {"already": False},
        "wall": {"ok": False},
        "missing": ["mysql"],
        "reuse": ["python", "mill"],
    }
    plan = ensure_deps_plan(probe=probe, nt=False, wsl=True)
    reasons = " ".join(a.get("reason", "") for a in plan["actions"]).lower()
    assert "hijack" in reasons or "3306" in reasons
    blob = " ".join(" ".join(c) for c in plan["cmds"]).lower()
    assert "mysql-community-server" in blob
    assert "mariadb-server" not in blob


def test_ensure_deps_dry_run_no_install():
    called = []

    def boom(cmd):
        called.append(cmd)
        raise AssertionError("dry-run must not run installs")

    row = ensure_deps(
        apply=False,
        run_cmd=boom,
        probe={
            "platform": {"nt": True, "wsl": False, "os": "windows"},
            "python": {"ok": False},
            "mill": {"ok": False},
            "mysql": {"ok": False},
            "dest": {"already": False},
            "wall": {"ok": False},
            "missing": ["python", "mill", "mysql"],
            "reuse": [],
        },
    )
    assert row["dry_run"] is True
    assert row["mutated"] is False
    assert called == []
    assert row["plan"]["cmds"]


def test_ensure_deps_apply_install_only_missing():
    ran = []

    class R:
        returncode = 0
        stdout = "ok"
        stderr = ""

    def fake(cmd):
        ran.append(list(cmd))
        return R()

    row = ensure_deps(
        apply=True,
        run_cmd=fake,
        probe={
            "platform": {"nt": True, "wsl": False, "os": "windows"},
            "python": {"ok": True},
            "mill": {"ok": True},
            "mysql": {"ok": False},
            "dest": {"already": False},
            "wall": {"ok": False},
            "missing": ["mysql"],
            "reuse": ["python", "mill"],
        },
    )
    assert row["ok"] is True
    assert any("Oracle.MySQL" in " ".join(c) for c in ran)
    assert not any("Lounge" in " ".join(c) for c in ran)
    assert not any("Python.Python" in " ".join(c) for c in ran)


def test_ensure_deps_access_denied_fail_closed():
    class R:
        returncode = 5
        stdout = ""
        stderr = "Access is denied."

    buf = __import__("io").StringIO()
    import agent_coord.install as inst

    old = inst.sys.stderr
    inst.sys.stderr = buf
    try:
        row = ensure_deps(
            apply=True,
            run_cmd=lambda cmd: R(),
            probe={
                "platform": {"nt": True, "wsl": False, "os": "windows"},
                "python": {"ok": True},
                "mill": {"ok": True},
                "mysql": {"ok": True},
                "dest": {"already": False},
                "wall": {"ok": False},
                "missing": ["mysql"],
                "reuse": ["python", "mill"],
            },
        )
    finally:
        inst.sys.stderr = old
    assert row["ok"] is False
    assert any("FAILED" in f for f in row["failed"])
    assert any("console" in f.lower() for f in row["failed"])
    assert "Access Denied" in buf.getvalue() or "access denied" in " ".join(row["failed"]).lower()


def test_bootstrap_scripts_exist_mention_python_mill_install_server():
    root = Path(__file__).resolve().parents[2]
    ps1 = (root / "scripts" / "bootstrap.ps1").read_text(encoding="utf-8")
    sh = (root / "scripts" / "bootstrap.sh").read_text(encoding="utf-8")
    for body in (ps1, sh):
        low = body.lower()
        assert "python" in low
        assert "mill" in low
        assert "install server" in low
    assert "winget" in ps1.lower() and "--disable-interactivity" in ps1
    assert "apt-get" in sh or "dnf" in sh or "apk" in sh
    assert "hijack" in sh.lower() or "3306" in sh


def test_probe_deps_reuse_when_services_running():
    pr = probe_deps(
        nt=True,
        wsl=False,
        py_version=(3, 12, 0),
        mill_on_path=True,
        mysql_service_state="RUNNING",
        wall_service_state="RUNNING",
        httpd={"nginx": r"C:\nginx\nginx.exe"},
        book_services=[{"name": "MySQL84", "status": "Running", "start_type": "Automatic"}],
        office={
            "dest": "C:/tmp/.mill",
            "config": "C:/tmp/.mill/config.toml",
            "config_exists": False,
            "www_exists": False,
            "vhost_exists": False,
            "already": False,
        },
    )
    assert "python" in pr["reuse"] and "python" not in pr["missing"]
    assert "mill" in pr["reuse"]
    assert "mysql" in pr["reuse"]
    assert pr["missing"] == []


def test_human_warn_no_installer_wizards_windows():
    blob = "\n".join(human_install_warn_lines(nt=True, wsl=False)).lower()
    assert "wizard" not in blob
    assert "installer wizards" not in blob


def test_write_role_server_dry_run_includes_ensure_deps_plan(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        "agent_coord.install.host.preflight_server",
        lambda **kwargs: {
            "ok_apply": False,
            "verdict": "missing-deps",
            "hints": ["need mysql"],
            "platform": {"nt": True, "wsl": False, "os": "windows"},
            "plan": {"dest": str(tmp_path), "would_write": []},
        },
    )
    monkeypatch.setattr(
        "agent_coord.install.host.ensure_deps_plan",
        lambda **kwargs: {
            "probe": {"missing": ["mysql"], "reuse": ["python"]},
            "actions": [{"piece": "mysql", "action": "install", "cmd": winget_install_argv(WINGET_MYSQL_ID)}],
            "cmds": [winget_install_argv(WINGET_MYSQL_ID)],
            "silent": True,
            "wizard": False,
        },
    )
    buf = __import__("io").StringIO()
    monkeypatch.setattr("agent_coord.install.sys.stderr", buf)
    monkeypatch.setattr(
        "agent_coord.install.host.print_human_install_warn",
        lambda **kwargs: human_install_warn_lines(nt=True, wsl=False),
    )
    row = write_role("server", dest=tmp_path / "o", dry_run=True)
    assert row.get("dry_run") is True
    assert row.get("mutated") is False
    ed = row.get("ensure_deps") or (row.get("plan") or {}).get("ensure_deps")
    assert ed
    flat = " ".join(" ".join(c) for c in ed.get("cmds") or [])
    assert "--disable-interactivity" in flat
    assert "wizard" not in "\n".join(row.get("human_warn") or []).lower()
