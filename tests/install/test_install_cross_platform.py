# -*- coding: utf-8 -*-
"""Plan #16+#18: mill-only uninstall + slash-compat paths.

JOB: cross-platform-install-paths
"""
from __future__ import annotations

from pathlib import Path, PurePosixPath

from agent_coord.install import (
    slash_compat_path,
    systemd_unit,
    uninstall_plan,
)
from agent_coord.client.tokens import drvfs_windows_path

from test_install_uninstall import _probe


ROOT = Path(__file__).resolve().parents[2]


def test_mill_uninstall_is_mill_wall_only():
    plan = uninstall_plan(
        probe=_probe(mysql_ok=True, wall_ok=True),
        dest=False,
        packages=False,
        nt=True,
    )
    pieces = {a["piece"]: a["action"] for a in plan["actions"]}
    assert pieces["mill-wall"] == "unregister"
    blob = " ".join(" ".join(c) for c in plan["cmds"])
    assert "mill-wall" in blob
    assert "winget" not in blob


def test_packages_flag_does_not_tear_os_httpd():
    plan = uninstall_plan(
        probe=_probe(mysql_ok=True, wall_ok=True),
        dest=False,
        packages=True,
        nt=True,
    )
    pieces = {a["piece"]: a["action"] for a in plan["actions"]}
    assert pieces["packages"] == "skip"
    blob = " ".join(" ".join(str(x) for x in c) for c in plan["cmds"])
    assert "winget" not in blob


def test_linux_uninstall_no_sc_winget():
    probe = _probe(mysql_ok=True, wall_ok=True)
    probe["platform"] = {"nt": False, "wsl": False, "os": "linux"}
    mill_only = uninstall_plan(probe=probe, dest=False, packages=False, nt=False)
    blob = " ".join(" ".join(str(x) for x in c) for c in mill_only["cmds"])
    assert "sc" not in blob
    assert "winget" not in blob
    assert "schtasks" not in blob
    assert "systemctl" in blob
    pieces = {a["piece"]: a["action"] for a in mill_only["actions"]}
    assert pieces["mill-wall"] == "unregister"
    packed = uninstall_plan(probe=probe, dest=False, packages=True, nt=False)
    pblob = " ".join(" ".join(str(x) for x in c) for c in packed["cmds"])
    assert "winget" not in pblob
    assert "sc" not in pblob


def test_slash_compat_tmp_path(tmp_path: Path):
    mixed = str(tmp_path).replace("\\", "/") + "/office"
    p = slash_compat_path(mixed)
    p.mkdir(parents=True)
    assert p.is_dir()
    back = str(tmp_path) + "\\other"
    p2 = slash_compat_path(back)
    p2.mkdir(parents=True)
    assert p2.is_dir()


def _dotted(*octets: int) -> str:
    return ".".join(str(n) for n in octets)


def test_check_pack_documentation_address_only() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "check_pack", ROOT / "tools" / "check_pack.py"
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    forbidden = _dotted(192, 168, 1, 50)
    public = _dotted(1, 2, 3, 4)
    assert mod.text_has_forbidden_address(f"mill join https://{forbidden}/")
    assert mod.text_has_forbidden_address(f"see {public}")
    assert not mod.text_has_forbidden_address('if ip.startswith("192.168.1."):')
    assert not mod.text_has_forbidden_address("GRANT mill@192.168.1.%")
    assert not mod.text_has_forbidden_address("192.168.1.*")
    assert not mod.text_has_forbidden_address("https://203.0.113.10/")
    assert not mod.text_has_forbidden_address("https://192.0.2.10/")
    assert not mod.text_has_forbidden_address("https://198.51.100.10/")
    assert not mod.text_has_forbidden_address("https://127.0.0.1/")
    assert not mod.text_has_forbidden_address("bind 0.0.0.0")
    assert not mod.text_has_forbidden_address("::1")
    assert not mod.text_has_forbidden_address("2001:db8::1")
    v6 = ":".join(("2606", "4700", "4700")) + "::" + "1111"
    assert mod.text_has_forbidden_address(v6)
    src = (ROOT / "tools" / "check_pack.py").read_text(encoding="utf-8")
    assert not mod.text_has_forbidden_address(src)
    assert forbidden not in src
    assert "non-documentation address in:" in src
    assert mod.scan_git_tracked(()) == []
    assert mod.scan_git_messages() == []
    assert mod.text_mark(chr(0x2014)) == 0x2014
    assert mod.text_mark(chr(0xFEFF) + "hello") == 0xFEFF
    assert mod.text_mark("s.lstrip(\"\\ufeff\").strip()") is None
    assert mod.text_mark(src) is None
    assert mod._is_text_file("agent_coord/client/outbound/__init__.py")
    assert mod._is_text_file("docs/dev/BUILD.md")
    assert mod._is_text_file("agent_coord/web/wall_ui/default/favicon.svg")
    assert not mod._is_text_file("images/icon.png")
    assert not mod._is_text_file("agent_coord/web/static/font.woff2")


def test_local_home_user_scan_from_disk_not_wordlist(tmp_path, monkeypatch) -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "check_pack", ROOT / "tools" / "check_pack.py"
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    src = (ROOT / "tools" / "check_pack.py").read_text(encoding="utf-8")
    fake = tmp_path / "Users"
    (fake / "packhygienetestuser").mkdir(parents=True)
    (fake / "Public").mkdir()
    monkeypatch.setattr(mod, "local_home_user_names", lambda: ("packhygienetestuser",))
    pats = mod._home_user_regexes(("packhygienetestuser",))
    assert mod._has_local_home_user("hello PackHygieneTestUser there", pats)
    assert not mod._has_local_home_user("packhygienetestuserish", pats)
    assert "packhygienetestuser" not in src
    assert "C:\\\\Users" in src or "C:\\Users" in src


def test_place_names_come_from_disk_not_wordlist(tmp_path, monkeypatch) -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "check_pack", ROOT / "tools" / "check_pack.py"
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    monkeypatch.delenv("GITLAB_CI", raising=False)
    monkeypatch.setenv("CI", "")
    monkeypatch.setenv("COMPUTERNAME", "packhygienehost")
    alias = tmp_path / "alias"
    alias.mkdir()
    (alias / "pack-hygiene-alias").write_text("203.0.113.10\n", encoding="utf-8")
    (alias / "lan").write_text("198.51.100.10\n", encoding="utf-8")
    monkeypatch.setattr(mod, "_alias_dir", lambda: alias)
    names = set(mod.local_place_names())
    assert names == {"packhygienehost", "pack-hygiene-alias"}
    monkeypatch.setenv("GITLAB_CI", "true")
    assert mod.local_place_names() == ()
    src = (ROOT / "tools" / "check_pack.py").read_text(encoding="utf-8")
    assert "packhygienehost" not in src
    assert "pack-hygiene-alias" not in src


def test_drvfs_and_home_markers() -> None:
    assert drvfs_windows_path("/mnt/c/office") == "C:\\office"
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "check_pack", ROOT / "tools" / "check_pack.py"
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    src = (ROOT / "tools" / "check_pack.py").read_text(encoding="utf-8")
    assert mod.HOME_MARKERS
    for marker in mod.HOME_MARKERS:
        if marker in src:
            continue
        assert marker.replace("\\", "\\\\") in src

def test_systemd_unit_contract():
    text = systemd_unit(
        python="python3",
        bind="127.0.0.1",
        port=18765,
        cwd=Path("/tmp/mill"),
        api_only=True,
        user="milluser",
        mill_home=PurePosixPath("/home/example/.mill"),
        pythonpath="/home/example/.local/lib/python3.13/site-packages",
    )
    assert "ExecStart=" in text
    assert "agent_coord wall" in text
    assert "--api-only" in text
    assert "User=milluser" in text
    assert "Environment=AGENT_COORD_MILL_HOME=/home/example/.mill" in text
    assert "Environment=PYTHONPATH=/home/example/.local/lib/python3.13/site-packages" in text
