# -*- coding: utf-8 -*-
"""OOTB mill uninstall (probe-first; dry-run default; no live --apply).

JOB: ootb-uninstall-cmd
"""
from __future__ import annotations

from pathlib import Path

from agent_coord.install import (
    WINGET_MYSQL_ID,
    WINGET_PYTHON_ID,
    elevate_windows_scm_helper_argv,
    packaged_scripts_dir,
    uninstall,
    uninstall_office,
    uninstall_plan,
    winget_uninstall_argv,
    windows_scm_unregister_ps1,
    write_windows_scm_unhelper,
)


ROOT = Path(__file__).resolve().parents[2]


def _probe(
    *,
    mysql_ok: bool = False,
    wall_ok: bool = False,
    dest_already: bool = False,
    dest: str = "C:/tmp/mill-office-test",
    leftover: list | None = None,
) -> dict:
    return {
        "platform": {"nt": True, "wsl": False, "os": "windows"},
        "python": {"ok": True, "version": [3, 12, 0]},
        "mill": {"ok": True, "path": "mill"},
        "mysql": {
            "ok": mysql_ok,
            "service": "MySQL84",
            "state": "RUNNING" if mysql_ok else "ABSENT",
            "bins": {},
            "services": [{"name": "MySQL84"}] if mysql_ok else [],
        },
        "wall": {
            "ok": wall_ok,
            "service": "mill-wall",
            "state": "RUNNING" if wall_ok else "ABSENT",
        },
        "mill_wall": {
            "ok": wall_ok,
            "service": "mill-wall",
            "state": "RUNNING" if wall_ok else "ABSENT",
        },
        "dest": {
            "dest": dest,
            "already": dest_already,
            "config_exists": dest_already,
            "www_exists": dest_already,
            "vhost_exists": dest_already,
        },
        "leftover_console": list(leftover or []),
        "missing": [],
        "reuse": [],
    }


def test_uninstall_plan_skips_absent_acts_present():
    absent = uninstall_plan(probe=_probe(), dest=False, packages=False, nt=True)
    assert "mill-wall" in absent["skip"]
    assert "mysql" in absent["skip"]
    assert absent["reuse"] == []
    present = uninstall_plan(
        probe=_probe(mysql_ok=True, wall_ok=True),
        dest=False,
        packages=False,
        nt=True,
    )
    assert "mill-wall" in present["reuse"]
    assert "mysql" not in present["reuse"]
    pieces = {a["piece"]: a["action"] for a in present["actions"]}
    assert pieces["mill-wall"] == "unregister"
    assert pieces["mysql"] == "skip"
    assert pieces["python"] == "keep"


def test_dry_run_mutates_nothing(tmp_path: Path):
    marker = tmp_path / "keep-me.txt"
    marker.write_text("x", encoding="utf-8")
    ran: list[list[str]] = []

    def runner(argv):
        ran.append(list(argv))
        class R:
            returncode = 0
            stderr = ""
            stdout = ""
        return R()

    out = uninstall(
        apply=False,
        dest=True,
        packages=True,
        probe=_probe(mysql_ok=True, wall_ok=True, dest_already=True, dest=str(tmp_path)),
        dest_path=tmp_path,
        nt=True,
        run_cmd=runner,
    )
    assert out["dry_run"] is True
    assert out["mutated"] is False
    assert ran == []
    assert marker.is_file()
    # alias
    out2 = uninstall_office(apply=False, dest_wipe=True, packages=True, probe=_probe(), nt=True)
    assert out2["dry_run"] is True
    assert out2["mutated"] is False


def test_dest_wipe_and_packages_flags_only_when_set(tmp_path: Path):
    base = _probe(mysql_ok=True, dest_already=True, dest=str(tmp_path))
    no_flags = uninstall_plan(probe=base, dest=False, packages=False, dest_path=tmp_path, nt=True)
    assert no_flags["dest"] is False
    assert no_flags["packages"] is False
    assert any(a["piece"] == "dest" and a["action"] == "skip" for a in no_flags["actions"])
    assert any(a["piece"] == "packages" and a["action"] == "skip" for a in no_flags["actions"])

    with_flags = uninstall_plan(probe=base, dest=True, packages=True, dest_path=tmp_path, nt=True)
    assert with_flags["dest"] is True
    assert with_flags["packages"] is True
    assert any(a["piece"] == "dest" and a["action"] == "wipe" for a in with_flags["actions"])
    assert any(a["piece"] == "packages" and a["action"] == "skip" for a in with_flags["actions"])


def test_uninstall_cmd_calls_mill_and_fallback_ps1():
    cmd = (ROOT / "scripts" / "uninstall.cmd").read_text(encoding="utf-8", errors="replace")
    low = cmd.lower()
    assert "mill uninstall --apply" in low
    assert "python -m agent_coord uninstall --apply" in low
    assert "uninstall.ps1" in low
    assert "windowstyle hidden" not in low  # whole run stays visible
    assert "pause" in low
    assert "cmd /k" in low
    assert "MILL_AGENT" in cmd
    ps1 = (ROOT / "scripts" / "uninstall.ps1").read_text(encoding="utf-8", errors="replace")
    assert "RunAs" in ps1
    assert "Hidden" in ps1
    assert "-Wait" in ps1 or " -Wait " in ps1
    assert "unregister-windows-services.ps1" in ps1


def test_unregister_helper_hidden_auto_exit_no_pause():
    helper = windows_scm_unregister_ps1()
    low = helper.lower()
    assert "mill-wall" in low
    assert "exit 0" in helper
    assert "pause" not in low
    assert "read-host" not in low
    assert "schtasks" in low and "delete" in low
    argv = elevate_windows_scm_helper_argv(
        Path(r"C:\dest\unregister-windows-services.ps1"), already_admin=False
    )
    blob = " ".join(argv)
    assert "Hidden" in argv or "Hidden" in blob
    assert "RunAs" in blob
    assert "-Wait" in blob
    admin_argv = elevate_windows_scm_helper_argv(
        Path(r"C:\dest\unregister-windows-services.ps1"), already_admin=True
    )
    admin_blob = " ".join(admin_argv)
    assert "-File" in admin_argv
    assert "Hidden" not in admin_argv and "Hidden" not in admin_blob
    assert "RunAs" not in admin_blob
    assert "Start-Process" not in admin_blob
    # synced repo script
    script = (ROOT / "scripts" / "unregister-windows-services.ps1").read_text(encoding="utf-8")
    assert "mill-wall" in script
    assert "exit 0" in script
    assert "pause" not in script.lower()
    path = write_windows_scm_unhelper(ROOT / "tmp" / "unhelper-test")
    assert path.name == "unregister-windows-services.ps1"
    assert "exit 0" in path.read_text(encoding="utf-8")


def test_packaged_scripts_and_pyproject():
    pkg = packaged_scripts_dir()
    assert pkg == (ROOT / "agent_coord" / "install" / "scripts")
    for name in (
        "install.cmd",
        "uninstall.cmd",
        "uninstall.ps1",
        "bootstrap.ps1",
        "bootstrap.sh",
        "register-windows-services.ps1",
        "unregister-windows-services.ps1",
    ):
        assert (pkg / name).is_file(), name
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "scripts/*" in pyproject


def test_join_human_mention_uninstall():
    join = (ROOT / "docs" / "JOIN.md").read_text(encoding="utf-8")
    assert "mill connect" in join
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "uninstall.cmd" in readme
    assert "mill uninstall" in readme


def test_winget_uninstall_argv_silent_no_python():
    mysql = winget_uninstall_argv(WINGET_MYSQL_ID)
    for argv in (mysql,):
        blob = " ".join(argv)
        assert argv[1] == "uninstall"
        assert "--disable-interactivity" in argv
        assert "--accept-package-agreements" in argv or "--accept-source-agreements" in argv
        assert WINGET_PYTHON_ID not in blob
        assert "Python.Python" not in blob
    assert "--override" in mysql
    assert "/quiet" in " ".join(mysql)
    assert "/norestart" in " ".join(mysql)
# extra tests appended by ootb-uninstall-redact

def test_redact_user_paths_hides_home():
    from agent_coord.install import redact_user_paths
    home = str(Path.home())
    blob = redact_user_paths({
        "dest": home + "/.mill",
        "bin": home + r"\AppData\Local\Programs\Python\python.exe",
        "nested": [home + "/foo"],
    })
    raw = str(blob)
    assert home not in raw
    assert "~" in raw
    # no drive-user leftover like Users\\name when home was that
    assert "Users\\" + Path.home().name not in raw.replace("/", "\\")


def test_uninstall_plan_sees_wall_key_without_mill_wall():
    probe = _probe(wall_ok=True, mysql_ok=False)
    probe.pop("mill_wall", None)
    plan = uninstall_plan(probe=probe, dest=False, packages=False, nt=True)
    assert "mill-wall" in plan["reuse"]
    pieces = {a["piece"]: a["action"] for a in plan["actions"]}
    assert pieces["mill-wall"] == "unregister"


def test_uninstall_apply_one_scm_pass_no_second_sc(tmp_path, monkeypatch):
    ran = []

    def runner(argv):
        ran.append(list(argv))
        class R:
            returncode = 0
            stderr = ""
            stdout = ""
        return R()

    monkeypatch.setattr("agent_coord.install.windows_is_admin", lambda: True)
    monkeypatch.setattr("agent_coord.install.write_windows_scm_unhelper", lambda dest: tmp_path / "unregister-windows-services.ps1")
    (tmp_path / "unregister-windows-services.ps1").write_text("# helper\n", encoding="utf-8")
    out = uninstall(
        apply=True,
        dest=False,
        packages=False,
        probe=_probe(mysql_ok=True, wall_ok=True),
        dest_path=tmp_path,
        nt=True,
        run_cmd=runner,
    )
    assert out["ok"] is True
    sc_stops = [a for a in ran if a[:2] == ["sc", "stop"]]
    assert sc_stops == []
    assert any("one SCM pass" in x for x in out["applied"])



def test_format_uninstall_lines_short_no_home_paths():
    from agent_coord.install import format_uninstall_lines
    home = str(Path.home())
    result = {
        "ok": True,
        "dry_run": False,
        "mutated": True,
        "failed": [],
        "applied": ["rmtree " + home + "/.mill"],
        "dest": True,
        "packages": False,
        "plan": {
            "actions": [
                {"piece": "python", "action": "keep"},
                {"piece": "mill-wall", "action": "skip"},
                {"piece": "dest", "action": "wipe"},
            ]
        },
    }
    lines = format_uninstall_lines(result)
    blob = "\n".join(lines)
    assert "mill uninstall: ok" in blob
    assert "kept: python" in blob
    assert "removed: dest" in blob
    assert "skipped: mill-wall" in blob
    assert home not in blob
    assert "{" not in blob
