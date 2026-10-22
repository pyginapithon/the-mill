"""Source of the Wall boot code for text checks (#710).

boot.js keeps the shared core; a split pane's paint code lives in its own
lazy file (``default/<pane>/<pane>-paint.js``, lib/lazy.js MODULES). Text
checks that are about the boot code as a whole read both.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "agent_coord" / "web" / "wall_ui"
BOOT = ROOT / "default" / "boot.js"


def pane_paint_files() -> list[Path]:
    """The split pane paint files, in a stable order."""
    return sorted(p for p in (ROOT / "default").glob("*/*-paint.js") if p.parent.name != "floor" or p.name != "map-paint.js")


def boot_source() -> str:
    """boot.js followed by every split pane paint file."""
    parts = [BOOT.read_text(encoding="utf-8")]
    parts += [p.read_text(encoding="utf-8") for p in pane_paint_files()]
    return "\n".join(parts)
