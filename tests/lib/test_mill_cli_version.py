# -*- coding: utf-8 -*-
"""Plan #27: mill --version from importlib.metadata, one line; the pack version is not a git SHA.

A build that is not a release adds +g<sha7> to the printed line (#538, F61).
"""
from __future__ import annotations

import io
from contextlib import redirect_stdout

import pytest

from agent_coord.__main__ import main, package_version
from agent_coord.install.packver import version_line


def test_package_version_not_git_sha():
    ver = package_version()
    assert ver
    assert "\n" not in ver
    assert "git" not in ver.lower()
    assert "." in ver or ver == "0+local"


def test_mill_version_flag_one_line():
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = main(["--version"])
    assert code == 0
    out = buf.getvalue().strip()
    assert out
    assert "\n" not in out
    assert out == version_line() and out.startswith(package_version())


def test_mill_short_version_flag():
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = main(["-V"])
    assert code == 0
    assert buf.getvalue().strip() == version_line()
