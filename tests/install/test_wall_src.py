# -*- coding: utf-8 -*-
from pathlib import Path

from agent_coord.install import mill_git_root, mill_wall_src, wall_ui_from_src


def test_wall_src_env_pip(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("MILL_WALL_SRC", "pip")
    monkeypatch.delenv("MILL_GIT_ROOT", raising=False)
    assert mill_wall_src() == "pip"
    ui = wall_ui_from_src("pip")
    assert ui.name == "default"


def test_wall_src_env_git(monkeypatch, tmp_path: Path):
    ui = tmp_path / "agent_coord" / "web" / "wall_ui" / "default"
    ui.mkdir(parents=True)
    (ui / "board.html").write_text("<html></html>", encoding="utf-8")
    monkeypatch.setenv("MILL_GIT_ROOT", str(tmp_path))
    monkeypatch.setenv("MILL_WALL_SRC", "git")
    assert mill_git_root() == tmp_path.resolve()
    assert wall_ui_from_src("git") == ui.resolve()
