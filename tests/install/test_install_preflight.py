"""Table-driven install preflight + WSL no-hijack (no live mill).

JOBs: install-preflight-detect, install-wsl-no-hijack, ootb-dogfood-fix-first
SoR: ACCEPTANCE-OOTB-INSTALL-FIRST-SLICE + PREFLIGHT + OOTB-INSTALL-WSL + ACCEPTANCE-OOTB-DOGFOOD-FIX-FIRST
"""
from __future__ import annotations

from pathlib import Path

import pytest

from agent_coord.install.host import (
    PREFLIGHT_VERDICTS,
    _firewall_https,
    _is_foreign_windows_path,
    detect_httpd_bins,
    detect_platform,
    preflight_server,
    python_too_old,
    write_role,
)


@pytest.mark.parametrize(
    "platform,environ,proc_version,expect_os,expect_wsl",
    [
        ("win32", {}, None, "windows", False),
        ("linux", {}, "Linux version 6.x", "linux", False),
        ("linux", {"WSL_DISTRO_NAME": "Ubuntu"}, None, "wsl", True),
        ("linux", {}, "Linux version 5.15.0-microsoft-standard-WSL2", "wsl", True),
        ("darwin", {}, None, "darwin", False),
    ],
)
def test_detect_platform_table(platform, environ, proc_version, expect_os, expect_wsl):
    got = detect_platform(platform=platform, environ=environ, proc_version=proc_version)
    assert got["os"] == expect_os
    assert got["wsl"] is expect_wsl
    assert got["nt"] is platform.startswith("win")


@pytest.mark.parametrize(
    "path,nt,expect",
    [
        (r"C:\nginx\nginx.exe", False, True),
        ("/mnt/c/nginx/nginx.exe", False, True),
        ("/usr/sbin/nginx", False, False),
        (r"C:\nginx\nginx.exe", True, False),
        ("nginx.exe", False, True),
    ],
)
def test_foreign_windows_path(path, nt, expect):
    assert _is_foreign_windows_path(path, nt=nt) is expect


def test_refuse_windows_httpd_from_wsl_which_map():
    bins = detect_httpd_bins(
        which_map={
            "nginx.exe": r"C:\nginx\nginx.exe",
            "nginx": "/mnt/c/nginx/nginx.exe",
        },
        candidates=[r"C:\nginx\nginx.exe", "/mnt/c/nginx/nginx.exe"],
        nt=False,
    )
    assert "nginx" not in bins


def test_accept_linux_nginx_on_posix():
    bins = detect_httpd_bins(
        which_map={"nginx": "/usr/sbin/nginx", "nginx.exe": r"C:\nginx\nginx.exe"},
        candidates=[r"C:\nginx\nginx.exe"],
        nt=False,
    )
    assert bins.get("nginx") == "/usr/sbin/nginx"


def test_windows_candidates_only_on_nt(tmp_path: Path, monkeypatch):
    # On NT, missing candidates simply absent; function must not pull POSIX-only.
    bins = detect_httpd_bins(which_map={}, candidates=[str(tmp_path / "nope.exe")], nt=True)
    assert bins == {}


@pytest.mark.parametrize(
    "book_present,reachable_ok,already,expect_verdict,ok_apply",
    [
        (False, True, False, "foreign-only", False),
        (False, False, False, "missing-deps", False),
        (True, True, False, "server-ready", True),
        (True, False, False, "server-ready", True),  # native service/bin enough
        (True, True, True, "already-configured", False),  # never green-light live --apply
        (False, True, True, "already-configured", False),
    ],
)
def test_preflight_verdicts_table(book_present, reachable_ok, already, expect_verdict, ok_apply):
    assert expect_verdict in PREFLIGHT_VERDICTS
    pf = preflight_server(
        platform_info={"os": "wsl", "platform": "linux", "wsl": True, "nt": False, "posix": True},
        httpd={},  # no Linux httpd - service mode still ok when book native
        book={"present": book_present, "services": [], "bins": {}},
        reachable={"ok": reachable_ok},
        office={
            "dest": "/var/tmp/mill-office",
            "config": "/var/tmp/mill-office/config.toml",
            "config_exists": already,
            "www_exists": False,
            "vhost_exists": False,
            "already": already,
        },
        host_windows_office=False,
    )
    assert pf["verdict"] == expect_verdict
    assert pf["ok_apply"] is ok_apply
    assert "plan" in pf
    if expect_verdict == "foreign-only":
        assert any("client" in h.lower() or "join" in h.lower() for h in pf["hints"])


def test_preflight_foreign_mysql_wsl_hints():
    pf = preflight_server(
        platform_info={"os": "wsl", "platform": "linux", "wsl": True, "nt": False, "posix": True},
        httpd={"nginx": r"C:\nginx\nginx.exe"},
        book={"present": False, "services": [], "bins": {}},
        reachable={"ok": True},
        office={
            "dest": "/tmp/x",
            "config": "/tmp/x/config.toml",
            "already": False,
            "config_exists": False,
            "www_exists": False,
            "vhost_exists": False,
        },
    )
    assert pf["verdict"] == "foreign-only"
    assert pf["ok_apply"] is False


def test_firewall_https_skips_on_non_windows(monkeypatch):
    monkeypatch.setattr("agent_coord.install.os.name", "posix")
    out = _firewall_https()
    assert out == ["firewall skipped (non-Windows)"]


def test_dry_run_mutates_nothing(tmp_path: Path):
    from agent_coord.install import write_role

    dest = tmp_path / "office"
    # Inject via preflight by using empty dest (no config) + mocked env not needed:
    # call write_role dry_run=True - must not create dest files even if verdict would allow writes.
    # Force foreign-only path first (no native book): still no mutate.
    row = write_role("server", dest=dest, apply=False, dry_run=True)
    assert row.get("dry_run") is True
    assert row.get("mutated") is False
    assert "plan" in row and "preflight" in row
    assert row.get("verdict") in PREFLIGHT_VERDICTS
    assert not dest.exists() or not any(dest.iterdir())


def test_dry_run_and_apply_exclusive(tmp_path: Path):
    from agent_coord.install import write_role

    row = write_role("server", dest=tmp_path / "o", apply=True, dry_run=True)
    assert row.get("ok") is False
    assert row.get("dry_run") is True
    assert not (tmp_path / "o").exists() or not any((tmp_path / "o").iterdir())


@pytest.mark.parametrize("role", ["client", "desk", "book", "wall", "cloud", "check"])
def test_dry_run_all_roles_no_dest_writes(tmp_path: Path, role: str):
    dest = tmp_path / "office"
    row = write_role(role, dest=dest, apply=False, dry_run=True)
    assert row.get("dry_run") is True
    assert row.get("mutated") is False
    assert row.get("role") == role
    assert not dest.exists() or not any(dest.iterdir())
    assert not (dest / "desk.txt").exists()


def test_dry_run_client_no_desk_txt(tmp_path: Path):
    dest = tmp_path / "home-office"
    row = write_role("client", dest=dest, dry_run=True)
    assert row.get("mutated") is False
    assert list(dest.glob("**/*")) == [] if dest.exists() else True
    assert not (dest / "desk.txt").exists()


def test_dry_run_apply_exclusive_all_roles(tmp_path: Path):
    for role in ("client", "desk", "book", "server"):
        row = write_role(role, dest=tmp_path / role, apply=True, dry_run=True)
        assert row.get("ok") is False
        assert row.get("dry_run") is True
        assert row.get("mutated") is False
        assert not (tmp_path / role).exists() or not any((tmp_path / role).iterdir())


def test_already_configured_never_ok_apply_even_with_book():
    pf = preflight_server(
        platform_info={"os": "windows", "platform": "win32", "wsl": False, "nt": True, "posix": False},
        httpd={"nginx": r"C:\nginx\nginx.exe"},
        book={"present": True, "services": [{"name": "MySQL"}], "bins": {}},
        reachable={"ok": True},
        office={
            "dest": r"C:\ProgramData\mill-office",
            "config": r"C:\ProgramData\mill-office\config.toml",
            "already": True,
            "config_exists": True,
            "www_exists": True,
            "vhost_exists": True,
        },
    )
    assert pf["verdict"] == "already-configured"
    assert pf["ok_apply"] is False
    assert "python-too-old" in PREFLIGHT_VERDICTS


@pytest.mark.parametrize("ver", [(3, 8), (3, 9), (2, 7)])
def test_python_too_old_preflight(ver):
    pf = preflight_server(
        py_version=ver,
        platform_info={"os": "wsl", "platform": "linux", "wsl": True, "nt": False, "posix": True},
        httpd={},
        book={"present": True, "services": [], "bins": {}},
        reachable={"ok": True},
        office={"dest": "/tmp/x", "config": "/tmp/x/config.toml", "already": False},
    )
    assert pf["verdict"] == "python-too-old"
    assert pf["ok_apply"] is False
    assert any("uv" in h.lower() for h in pf["hints"])
    assert any("3.12" in h for h in pf["hints"])
    gate = python_too_old(py_version=ver)
    assert gate is not None and gate["verdict"] == "python-too-old"


@pytest.mark.parametrize("ver", [(3, 10), (3, 11), (3, 12)])
def test_python_ok_reaches_existing_verdicts(ver):
    assert python_too_old(py_version=ver) is None
    pf = preflight_server(
        py_version=ver,
        platform_info={"os": "wsl", "platform": "linux", "wsl": True, "nt": False, "posix": True},
        httpd={},
        book={"present": False, "services": [], "bins": {}},
        reachable={"ok": True},
        office={"dest": "/tmp/x", "config": "/tmp/x/config.toml", "already": False},
    )
    assert pf["verdict"] == "foreign-only"
    assert pf["ok_apply"] is False


def test_write_role_py38_refuses_clean_no_exception(tmp_path: Path):
    row = write_role("client", dest=tmp_path / "o", dry_run=True, py_version=(3, 8))
    assert row.get("ok") is False
    assert row.get("verdict") == "python-too-old"
    assert row.get("mutated") is False
    assert any("uv" in w.lower() for w in (row.get("warnings") or []))
    assert not (tmp_path / "o").exists()
