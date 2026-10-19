# -*- coding: utf-8 -*-
"""Plan #23: presence root = office dest; refuse System32/Windows/bare drive."""
from __future__ import annotations

from pathlib import Path

import pytest

from agent_coord.install.session_root import choose_root, default_root, refuse_reason


def test_refuse_system_and_drive_roots():
    assert refuse_reason("C:/Windows/System32")
    assert refuse_reason("C:/Windows")
    assert refuse_reason("C:/")
    assert refuse_reason("/")
    assert refuse_reason("/mnt/c/Windows")
    assert refuse_reason("/mnt/c/Windows/System32")
    assert refuse_reason("/mnt/c")


def test_allow_office_tmp(tmp_path: Path):
    office = tmp_path / "office"
    office.mkdir()
    assert refuse_reason(office) is None
    assert choose_root(office) == default_root(office)


def test_default_root_is_office_not_cwd(tmp_path: Path, monkeypatch):
    office = tmp_path / "office"
    office.mkdir()
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(office))
    monkeypatch.chdir(tmp_path)
    got = default_root()
    assert got.endswith("office") or got.endswith("office".replace("/", "\\"))
    cwd = str(tmp_path.resolve()).replace("\\", "/").rstrip("/")
    assert cwd not in got or got.replace("\\", "/").rstrip("/") != cwd


def test_choose_root_empty_uses_office(tmp_path: Path, monkeypatch):
    office = tmp_path / "office"
    office.mkdir()
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(office))
    got = choose_root(None)
    assert "office" in got.replace("\\", "/")


def test_choose_root_forbidden_raises():
    with pytest.raises(ValueError, match="refuse"):
        choose_root("C:/Windows/System32")
