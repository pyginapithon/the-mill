"""pack_local --help and import (no full build)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_pack_local_help() -> None:
    r = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "pack_local.py"), "--help"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "--install" in r.stdout
    assert "--notify" in r.stdout
    assert "PyPI" in r.stdout


def test_mill_cli_smoke_cmd_listed() -> None:
    sys.path.insert(0, str(ROOT / "tools"))
    import mill_cli_smoke

    help_text = "    connect  clock in\n    hold     mill hold\n"
    assert mill_cli_smoke._cmd_listed(help_text, "connect")
    assert mill_cli_smoke._cmd_listed(help_text, "hold")
    assert not mill_cli_smoke._cmd_listed(help_text, "leftover")
    assert not mill_cli_smoke._cmd_listed(help_text, "here")


def test_pack_local_redacted_home() -> None:
    sys.path.insert(0, str(ROOT / "tools"))
    import pack_local

    home_file = Path.home() / "dummy-wheel.whl"
    s = pack_local.redacted(home_file)
    assert s.startswith("~/")
    assert "Users" not in s
