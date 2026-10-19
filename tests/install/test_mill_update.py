"""Plan #17 mill update / pip bump (no MySQL, no wipe)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from agent_coord.install import (
    mill_source_tree,
    run_update,
    update_pip_cmd,
    update_plan,
    wall_service_state,
    with_session_hash,
)
from agent_coord.install.host import cmdline_is_connect

ROOT = Path(__file__).resolve().parents[2]


def test_with_session_hash() -> None:
    assert with_session_hash("https://203.0.113.1/") == "https://203.0.113.1/#session"
    assert with_session_hash("https://203.0.113.1/#session") == "https://203.0.113.1/#session"
    assert with_session_hash("https://203.0.113.1/#jobs") == "https://203.0.113.1/#jobs"


def test_update_pip_cmd_never_dot() -> None:
    cmd = update_pip_cmd()
    assert cmd[1:5] == ["-m", "pip", "install", "-U"]
    assert cmd[-1] == "the-mill"
    assert "." not in cmd
    assert "uninstall" not in cmd
    assert "MySQL" not in " ".join(cmd)
    system_python = os.name != "nt" and sys.prefix == getattr(sys, "base_prefix", sys.prefix)
    if system_python:
        assert "--break-system-packages" in cmd
    else:
        assert "--break-system-packages" not in cmd


def test_mill_source_tree_repo() -> None:
    assert mill_source_tree(ROOT) is True


def test_mill_source_tree_empty(tmp_path: Path) -> None:
    assert mill_source_tree(tmp_path) is False


def test_mill_source_tree_named(tmp_path: Path) -> None:
    (tmp_path / "agent_coord").mkdir()
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "the-mill"\n', encoding="utf-8")
    assert mill_source_tree(tmp_path) is True


def test_update_plan_refuses_source_tree(tmp_path: Path) -> None:
    (tmp_path / "agent_coord").mkdir()
    (tmp_path / "pyproject.toml").write_text('name = "the-mill"\n', encoding="utf-8")
    dest = tmp_path / "office"
    dest.mkdir()
    (dest / "config.toml").write_text("x=1\n", encoding="utf-8")
    plan = update_plan(cwd=tmp_path, dest=dest)
    assert plan["ok"] is False
    assert plan["refused"] == "mill-source-tree"
    assert plan["wipe"] is False
    assert plan["smash"] is False
    assert plan["dest_action"] == "keep"
    assert plan["cmd"][-1] != "."


def test_update_plan_non_git_cwd(tmp_path: Path) -> None:
    dest = tmp_path / "office"
    dest.mkdir()
    plan = update_plan(cwd=tmp_path, dest=dest)
    assert plan["ok"] is True
    assert plan["cmd"][1:5] == ["-m", "pip", "install", "-U"]
    assert plan["cmd"][-1] == "the-mill"
    assert "." not in plan["cmd"]
    system_python = os.name != "nt" and sys.prefix == getattr(sys, "base_prefix", sys.prefix)
    if system_python:
        assert "--break-system-packages" in plan["cmd"]
    else:
        assert "--break-system-packages" not in plan["cmd"]
    assert plan["wipe"] is False
    assert plan["smash"] is False
    assert plan["dest_action"] == "absent"


def test_run_update_dry_run_does_not_pip(tmp_path: Path) -> None:
    def runner(*_a, **_k):
        raise AssertionError("pip must not run on --dry-run")

    row = run_update(
        apply=False,
        cwd=tmp_path,
        dest=tmp_path,
        run_cmd=runner,
        private_ips=["198.51.100.23"],
    )
    assert row["ok"] is True
    assert row["applied"] is False
    assert row["dry_run"] is True
    assert row["share_urls"][0] == "https://198.51.100.23/#session"
    assert row["url"].endswith("#session")


class Proc:
    def __init__(self, code: int = 0, err: str = "", out: str = "") -> None:
        self.returncode = code
        self.stderr = err
        self.stdout = out


def _argv(cmd) -> list[str]:
    return [str(part).lower() for part in cmd]


def _is_wall_query(cmd) -> bool:
    argv = _argv(cmd)
    return "query" in argv or "is-active" in argv


def _is_wall_stop(cmd) -> bool:
    argv = _argv(cmd)
    return "mill-wall" in argv and "stop" in argv and not _is_wall_query(cmd)


def _is_wall_start(cmd) -> bool:
    argv = _argv(cmd)
    return "mill-wall" in argv and "start" in argv and not _is_wall_query(cmd)


def _is_import_check(cmd) -> bool:
    argv = [str(part) for part in cmd]
    return "-c" in argv and any("make_asgi_app" in part for part in argv)


def _no_connect() -> list[int]:
    return []


def _query_text(*, running: bool) -> str:
    # One blob covers Windows `sc query` and Linux `systemctl is-active`.
    if running:
        return "STATE              : 4  RUNNING\nactive\n"
    return "STATE              : 1  STOPPED\ninactive\n"


def test_wall_service_state_classifies_sc_and_systemctl() -> None:
    assert wall_service_state("STATE              : 1  STOPPED\n") == "stopped"
    assert wall_service_state("STATE              : 4  RUNNING\n") == "running"
    assert wall_service_state("STATE              : 3  STOP_PENDING\n") == "pending"
    assert wall_service_state("The specified service does not exist.\n") == "absent"
    assert wall_service_state("inactive\n", code=3) == "stopped"
    assert wall_service_state("active\n") == "running"
    assert wall_service_state("ok\n") == "unknown"


def test_run_update_apply_mocked(tmp_path: Path) -> None:
    seen: list[list[str]] = []
    phase = {"stopped": False}

    def runner(cmd, **kwargs):
        seen.append(list(cmd))
        if _is_wall_query(cmd):
            return Proc(out=_query_text(running=not phase["stopped"]))
        if _is_wall_stop(cmd):
            phase["stopped"] = True
            return Proc()
        return Proc()

    dest = tmp_path / "office"
    dest.mkdir()
    (dest / "config.toml").write_text("[office]\n", encoding="utf-8")
    row = run_update(
        apply=True,
        cwd=tmp_path,
        dest=dest,
        run_cmd=runner,
        private_ips=["203.0.113.9"],
        already_admin=True,
        stop_poll_s=0,
        connect_pids=_no_connect,
    )
    # Order: query running, stop, query STOPPED, pip, import, start.
    assert any(_is_wall_stop(c) for c in seen)
    pip_cmds = [c for c in seen if c and c[-1] == "the-mill"]
    assert pip_cmds, seen
    assert "-U" in pip_cmds[0]
    assert "." not in pip_cmds[0]
    assert any(c[-2:] == ["start", "mill-wall"] for c in seen)
    stop_i = next(i for i, c in enumerate(seen) if _is_wall_stop(c))
    pip_i = next(i for i, c in enumerate(seen) if c[-1] == "the-mill")
    import_i = next(i for i, c in enumerate(seen) if _is_import_check(c))
    start_i = next(i for i, c in enumerate(seen) if _is_wall_start(c))
    assert stop_i < pip_i < import_i < start_i
    assert seen[0] and _is_wall_query(seen[0])
    assert row["schema"] == "not-run"
    assert (dest / "config.toml").read_text(encoding="utf-8") == "[office]\n"
    assert row["ok"] is True
    assert row["applied"] is True
    assert row["pip_applied"] is True
    assert row["restart_ok"] is True
    assert row["dest_action"] == "keep"
    assert row["wipe"] is False
    assert row["smash"] is False
    assert row["url"] == "https://203.0.113.9/#session"
    assert any("Does not smash dest" in x or "mill-wall" in x for x in row["next"])
    assert any("#session" in x for x in row["next"])
    assert any("SKILL.md" in x for x in row["next"])


def test_run_update_refuses_pip_dot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "agent_coord.install.host.update_pip_cmd",
        lambda: [sys.executable, "-m", "pip", "install", "."],
    )
    row = run_update(apply=True, cwd=tmp_path, dest=tmp_path, private_ips=["203.0.113.1"])
    assert row["ok"] is False
    assert row["applied"] is False
    assert "pip install ." in (row.get("reason") or "")


def test_cli_update_dry_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    from agent_coord.__main__ import main

    rc = main(["update", "--dry-run"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "the-mill" in out
    assert "#session" in out
    assert "mill-source-tree" not in out


def test_run_update_does_not_pip_while_wall_running(tmp_path: Path) -> None:
    seen: list[list[str]] = []

    def runner(cmd, **kwargs):
        seen.append(list(cmd))
        if _is_wall_query(cmd):
            return Proc(out=_query_text(running=True))
        return Proc()

    row = run_update(
        apply=True,
        cwd=tmp_path,
        dest=tmp_path,
        run_cmd=runner,
        private_ips=["203.0.113.9"],
        already_admin=True,
        stop_wait_s=0,
        stop_poll_s=0,
        connect_pids=_no_connect,
    )
    assert row["ok"] is False
    assert row["pip_applied"] is False
    assert row["restart_ok"] is False
    assert row.get("wall_restart") == "skipped"
    assert "pip not run" in (row.get("error") or "")
    assert not any(c and c[-1] == "the-mill" for c in seen)
    assert any(_is_wall_stop(c) for c in seen)
    assert not any(_is_wall_start(c) for c in seen)


def test_run_update_absent_wall_still_pips(tmp_path: Path) -> None:
    seen: list[list[str]] = []

    def runner(cmd, **kwargs):
        seen.append(list(cmd))
        if _is_wall_query(cmd):
            return Proc(code=1060, err="The specified service does not exist.\n")
        return Proc()

    row = run_update(
        apply=True,
        cwd=tmp_path,
        dest=tmp_path,
        run_cmd=runner,
        private_ips=["203.0.113.9"],
        already_admin=True,
        stop_poll_s=0,
        connect_pids=_no_connect,
    )
    assert row["ok"] is True
    assert row["pip_applied"] is True
    assert not any(_is_wall_stop(c) for c in seen)
    assert any(c and c[-1] == "the-mill" for c in seen)


def test_run_update_restart_failure_reports_separately(tmp_path: Path) -> None:
    def runner(cmd, **kwargs):
        if _is_wall_query(cmd):
            return Proc(out=_query_text(running=False))
        if _is_wall_start(cmd):
            return Proc(1, "start failed")
        return Proc()

    dest = tmp_path / "office"
    dest.mkdir()
    (dest / "config.toml").write_text("[office]\n", encoding="utf-8")
    row = run_update(
        apply=True,
        cwd=tmp_path,
        dest=dest,
        run_cmd=runner,
        private_ips=["203.0.113.9"],
        already_admin=True,
        connect_pids=_no_connect,
    )
    assert row["pip_applied"] is True
    assert row["restart_ok"] is False
    assert row["ok"] is False
    assert row.get("wall_restart") == "failed"


def test_cmdline_is_connect() -> None:
    assert cmdline_is_connect(r"C:\Python\Scripts\mill.exe connect the-mill grok-tui")
    assert cmdline_is_connect("mill connect the-mill desk")
    assert not cmdline_is_connect(r"C:\Python\Scripts\mill.exe update")
    assert not cmdline_is_connect("mill.exe disconnect")


def test_run_update_refuses_when_connect_holds_mill_exe(tmp_path: Path) -> None:
    def runner(*_a, **_k):
        raise AssertionError("must not stop, pip, or start while a connect holds mill.exe")

    row = run_update(
        apply=True,
        cwd=tmp_path,
        dest=tmp_path,
        run_cmd=runner,
        private_ips=["203.0.113.9"],
        already_admin=True,
        connect_pids=lambda: [4242],
    )
    assert row["ok"] is False
    assert row["pip_applied"] is False
    assert row["restart_ok"] is False
    assert row.get("refused") == "connect-holds-mill"
    assert row.get("wall_restart") == "skipped"
    assert row.get("error") == "a running mill connect holds Scripts\\mill.exe; stop that connect before install"


def test_run_update_scan_failure_skips_pip(tmp_path: Path) -> None:
    def boom():
        raise OSError("scanner down")

    def runner(*_a, **_k):
        raise AssertionError("must not run when the connect scan fails")

    row = run_update(
        apply=True,
        cwd=tmp_path,
        dest=tmp_path,
        run_cmd=runner,
        private_ips=["203.0.113.9"],
        already_admin=True,
        connect_pids=boom,
    )
    assert row["ok"] is False
    assert row["pip_applied"] is False
    assert row.get("refused") == "connect-scan-failed"
    assert row.get("error") == "could not check for a running mill connect"


def test_run_update_pip_failure_does_not_start_wall(tmp_path: Path) -> None:
    seen: list[list[str]] = []

    def runner(cmd, **kwargs):
        seen.append(list(cmd))
        if _is_wall_query(cmd):
            return Proc(out=_query_text(running=False))
        if cmd and cmd[-1] == "the-mill":
            return Proc(1, "pip failed")
        return Proc()

    row = run_update(
        apply=True,
        cwd=tmp_path,
        dest=tmp_path,
        run_cmd=runner,
        private_ips=["203.0.113.9"],
        already_admin=True,
        stop_poll_s=0,
        connect_pids=_no_connect,
    )
    assert row["ok"] is False
    assert row["pip_applied"] is False
    assert row["restart_ok"] is False
    assert row.get("wall_restart") == "skipped"
    assert any(c and c[-1] == "the-mill" for c in seen)
    assert not any(_is_import_check(c) for c in seen)
    assert not any(_is_wall_start(c) for c in seen)


def test_run_update_import_failure_does_not_start_wall(tmp_path: Path) -> None:
    seen: list[list[str]] = []

    def runner(cmd, **kwargs):
        seen.append(list(cmd))
        if _is_wall_query(cmd):
            return Proc(out=_query_text(running=False))
        if _is_import_check(cmd):
            return Proc(1, "import failed")
        return Proc()

    row = run_update(
        apply=True,
        cwd=tmp_path,
        dest=tmp_path,
        run_cmd=runner,
        private_ips=["203.0.113.9"],
        already_admin=True,
        stop_poll_s=0,
        connect_pids=_no_connect,
    )
    assert row["pip_applied"] is True
    assert row["ok"] is False
    assert row["restart_ok"] is False
    assert row.get("wall_restart") == "skipped"
    assert row.get("error") == "import failed"
    assert any(_is_import_check(c) for c in seen)
    assert not any(_is_wall_start(c) for c in seen)


def test_run_update_refuses_when_not_admin(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import agent_coord.install.host as hostmod

    monkeypatch.setattr(hostmod, "update_requires_admin", lambda: True)
    monkeypatch.setattr(hostmod, "windows_is_admin", lambda: False)

    def boom(*_a, **_k):
        raise AssertionError("must not run when not admin")

    row = run_update(
        apply=True,
        cwd=tmp_path,
        dest=tmp_path,
        run_cmd=boom,
        private_ips=["203.0.113.1"],
        already_admin=False,
    )
    assert row["ok"] is False
    assert row["pip_applied"] is False
    assert row["restart_ok"] is False
    assert row.get("refused") == "not-admin"
