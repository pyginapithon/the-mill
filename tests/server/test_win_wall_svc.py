# -*- coding: utf-8 -*-
"""Regression: mill-wall SERVICE no-console + uvicorn Config must not isatty-crash."""
from __future__ import annotations

import sys

from agent_coord.server.win_wall_svc import _TeeIO, _no_console_stdio


def test_no_console_isatty(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    sys.stdout = None  # type: ignore[assignment]
    sys.stderr = None  # type: ignore[assignment]
    sys.__stdout__ = None  # type: ignore[assignment]
    sys.__stderr__ = None  # type: ignore[assignment]
    _no_console_stdio()
    assert sys.stdout is not None
    assert sys.stdout.isatty() is False
    assert sys.stderr.isatty() is False
    assert sys.__stdout__.isatty() is False
    sys.stdout.write("hello-out\n")
    sys.stderr.write("hello-err\n")
    out = (tmp_path / "mill-wall-svc-out.log").read_text(encoding="utf-8")
    assert "hello-out" in out
    assert "hello-err" in out


def test_tee_flush(tmp_path) -> None:
    p = tmp_path / "out.log"
    tee = _TeeIO(p, error=False)
    assert tee.isatty() is False
    tee.write("a")
    tee.write("b\n")
    assert p.read_text(encoding="utf-8") == "ab\n"


def test_uvicorn_config_headless(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    sys.stdout = None  # type: ignore[assignment]
    sys.stderr = None  # type: ignore[assignment]
    _no_console_stdio()
    import uvicorn

    cfg = uvicorn.Config(
        app=lambda scope, receive, send: None,
        host="127.0.0.1",
        port=9,
        log_level="info",
        access_log=False,
        use_colors=False,
        log_config=None,
    )
    assert cfg.use_colors is False
