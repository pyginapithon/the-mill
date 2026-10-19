# -*- coding: utf-8 -*-
"""PLAN #30: header clock is pack version, machine name, 24h local + tz."""
from __future__ import annotations

from pathlib import Path

from agent_coord.install.packver import package_version

BOOT = Path(__file__).resolve().parents[2] / "agent_coord" / "web" / "wall_ui" / "default" / "boot.js"


def test_packver_not_git_sha():
    ver = package_version()
    assert ver
    assert "\n" not in ver
    assert "git" not in ver.lower()
    assert "." in ver or ver == "0+local"


def test_boot_clock_order_and_24h():
    src = BOOT.read_text(encoding="utf-8")
    clock = src[src.index("function wallClockLine"): src.index("function paintWallClock")]
    assert "d.version || packVer" in clock
    assert "d.node || \"\"" in clock
    assert "wallClockNow()" in clock
    assert clock.index("d.version") < clock.index("d.node")
    assert clock.index("d.node") < clock.index("wallClockNow()")
    assert "hour12: false" in src
    assert "timeZoneName: \"short\"" in src
