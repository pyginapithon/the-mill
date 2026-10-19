"""mill connect real path (0.6.40 shipped a stale name after argparse).

Runs the connect body end to end in a subprocess against a closed local port,
the same check tools/mill_cli_smoke.py runs on the installed sdist.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _smoke():
    spec = importlib.util.spec_from_file_location("mill_cli_smoke", ROOT / "tools" / "mill_cli_smoke.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def test_connect_reaches_socket_loop(monkeypatch):
    monkeypatch.setenv("PYTHONPATH", str(ROOT))
    bad = _smoke().run_connect_real([sys.executable, "-m", "agent_coord"])
    assert bad == "", bad


def test_connect_is_a_real_path_row():
    assert "connect" in _smoke().RUN_ROWS


def test_no_spawn_leftover_in_connect():
    src = (ROOT / "agent_coord" / "client" / "http.py").read_text(encoding="utf-8")
    assert "if spawn:" not in src
