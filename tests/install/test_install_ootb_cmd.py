# -*- coding: utf-8 -*-
"""OOTB Windows install.cmd + mill-wall SERVICE (no live mill / no --apply).

JOB: ootb-install-cmd
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from agent_coord.install.host import (
    WINGET_MYSQL_ID,
    elevate_windows_scm_helper_argv,
    mill_wall_service_binpath,
    winget_install_argv,
    windows_scm_register_ps1,
    write_windows_scm_helper,
    _wall_task,
)


ROOT = Path(__file__).resolve().parents[2]


def test_install_cmd_exists_and_probes():
    cmd = (ROOT / "scripts" / "install.cmd").read_text(encoding="utf-8", errors="replace")
    low = cmd.lower()
    assert "python" in low
    assert "mill" in low
    assert "mill-wall" in low
    # 0.4 mill-wall is FastAPI.
    assert "mysql84" in low
    assert "mill-wall" in low
    assert "winget" in low
    assert "--disable-interactivity" in cmd
    assert "install server --apply" in low or "install server --apply" in cmd
    assert "start-process" in low and "runas" in low
    assert "windowstyle hidden" in low
    assert "-wait" in low
    assert "net session" in low
    assert "this window" in low
    assert '-file "%helper%"' in low
    assert "share_wall_urls" in low or "share url" in low
    assert "wall.crt" in low and "import" in low
    assert "localhost" in low or "127.0.0.1" in low or "trusted" in low or "proceed" in low
    assert "pause" in low
    assert "cmd /k" in low
    assert "MILL_AGENT" in cmd
    assert "do not execute it line by line" in low
    assert "curl -fssl" in low
    assert "https://raw.githubusercontent.com/pyginapithon/the-mill/main/scripts/install.cmd" in cmd
    assert "https://raw.githubusercontent.com/pyginapithon/the-mill/main/scripts/bootstrap.ps1" in cmd
    assert "install.cmd --agent" in cmd


def test_mysql_winget_argv_has_quiet_override():
    argv = winget_install_argv(WINGET_MYSQL_ID)
    blob = " ".join(argv)
    assert "--override" in argv
    assert "/quiet" in blob
    assert "/norestart" in blob
    assert "--disable-interactivity" in argv
    # install.cmd must mention the same override for Oracle.MySQL
    cmd = (ROOT / "scripts" / "install.cmd").read_text(encoding="utf-8", errors="replace")
    assert "Oracle.MySQL" in cmd
    assert "/quiet" in cmd


def test_elevate_launch_is_hidden_wait_auto_exit():
    argv = elevate_windows_scm_helper_argv(
        Path(r"C:\dest\register-windows-services.ps1"), already_admin=False
    )
    blob = " ".join(argv)
    assert "Hidden" in argv or "Hidden" in blob
    assert "RunAs" in blob
    assert "-Wait" in blob or " -Wait " in blob
    helper = windows_scm_register_ps1(python="python", bind="127.0.0.1", port=18765)
    assert "exit 0" in helper
    assert "pause" not in helper.lower()
    assert "read-host" not in helper.lower()


def test_elevate_already_admin_is_in_window_file():
    helper = Path(r"C:\dest\register-windows-services.ps1")
    argv = elevate_windows_scm_helper_argv(helper, already_admin=True)
    blob = " ".join(argv)
    assert "-File" in argv
    assert str(helper) in argv
    assert "Hidden" not in argv
    assert "Hidden" not in blob
    assert "RunAs" not in blob
    assert "Start-Process" not in blob
    extra = elevate_windows_scm_helper_argv(
        helper, extra_args='-Dest -DestPath "C:\\dest"', already_admin=True
    )
    assert extra[:6] == [
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(helper),
    ]
    assert "-Dest" in extra


def test_mill_wall_service_strings_not_only_schtasks():
    helper = windows_scm_register_ps1(python=r"C:\Python\python.exe", port=18765)
    low = helper.lower()
    assert "sc.exe create" in low or "sc create" in low
    assert "mill-wall" in low
    assert "win_wall_svc" in helper
    assert "service" in low
    # Must not be schtasks-only registration
    assert "schtasks /create" not in low
    assert "/sc onlogon" not in low
    binpath = mill_wall_service_binpath(python="python", bind="127.0.0.1", port=18765)
    assert "win_wall_svc" in binpath
    assert "win_wall_svc" in binpath
    assert "18765" in binpath


def test_helper_synced_in_scripts():
    script = (ROOT / "scripts" / "register-windows-services.ps1").read_text(encoding="utf-8")
    low = script.lower()
    assert "mill-wall" in low
    assert "sc" in low and "create" in low
    assert "exit 0" in script
    assert "pause" not in low
    assert "read-host" not in low
    assert "win_wall_svc" in script or "agent_coord.server.win_wall_svc" in script


def test_bootstrap_ps1_points_at_install_cmd():
    ps1 = (ROOT / "scripts" / "bootstrap.ps1").read_text(encoding="utf-8")
    assert "install.cmd" in ps1
    assert "winget" in ps1 and "--disable-interactivity" in ps1


def test_write_windows_scm_helper_includes_service(tmp_path: Path):
    path = write_windows_scm_helper(
        tmp_path, python="python", bind="127.0.0.1", port=18765, api_only=True
    )
    body = path.read_text(encoding="utf-8")
    assert "mill-wall" in body
    assert "sc.exe create" in body or "sc create" in body
    assert "exit 0" in body


def test_wall_task_prefers_service(monkeypatch):
    monkeypatch.setattr(
        "agent_coord.install.host._windows_service_state",
        lambda name: "RUNNING" if name == "mill-wall" else "ABSENT",
    )
    row = _wall_task()
    assert row["ok"] is True
    assert "SERVICE" in row["detail"]
    assert "schtasks" not in row["detail"].lower()


def test_join_mentions_install_cmd_and_grok_build():
    join = (ROOT / "docs" / "JOIN.md").read_text(encoding="utf-8")
    assert "mill connect" in join
    assert "howto-ai" in join or "Grok" in join
    boot = (ROOT / "docs" / "install" / "HOST.md").read_text(encoding="utf-8")
    assert "mill install" in boot
    assert (ROOT / "agent_coord" / "install" / "scripts" / "install.cmd").is_file()


@pytest.mark.skipif(os.name != "nt", reason="win_wall_svc import on Windows")
def test_win_wall_svc_module_importable():
    from agent_coord.server import win_wall_svc

    assert win_wall_svc.SERVICE_NAME == "mill-wall"
    assert hasattr(win_wall_svc, "main")
