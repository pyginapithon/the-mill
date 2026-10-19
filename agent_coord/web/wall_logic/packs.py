"""Fungible Wall pack seams (P0 layout + override points).

Product intent (human): Wall UI is **dynamic** - any mill user can tweak
the glance client and **share** with other office users. Default pack =
human layout (hopefully good enough). Stable book = mill API/CLI + pure
rules in `wall_logic`.

**Shipped today (P0):** `wall_ui/default/`, refresh-needed asset id,
prefs stub hooks. **Not shipped (P1 parked):** live in-browser tweak UI,
desk pack save/load, private|public marketplace, adopt/copy.

This module documents and tests **seams** so live-share is easy later -
it does not pretend marketplace is live.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

DEFAULT_PACK_ID = "default"


def wall_ui_root() -> Path:
    return Path(__file__).resolve().parent.parent / "wall_ui"


def default_pack_dir() -> Path:
    return wall_ui_root() / DEFAULT_PACK_ID


def default_board_path() -> Path:
    """SoR HTML for OOTB glance (prefer wall_ui/default over static/)."""
    p = default_pack_dir() / "board.html"
    if p.is_file():
        return p
    legacy = Path(__file__).resolve().parent.parent / "web" / "static" / "board.html"
    return legacy


def pack_seam_inventory() -> dict[str, Any]:
    """Inventory of fungibility seams - for unit tests + structure review.

    Flags distinguish shipped vs parked so tests do not claim live-share.
    """
    root = wall_ui_root()
    default = default_pack_dir()
    components = root / "components"
    board = default_board_path()
    return {
        "wall_ui_root": str(root),
        "default_pack_id": DEFAULT_PACK_ID,
        "fungibility_ladder": ("db_knobs", "pack_css_js_override", "office_share"),
        "knobs_do_not_replace_pack": True,
        "default_pack_dir": str(default),
        "default_board": str(board),
        "default_board_exists": board.is_file(),
        "components_dir": str(components),
        "components_ready": components.is_dir(),  # override/extract point
        "readme": str(root / "README.md"),
        "shipped": {
            "p0_folder_layout": root.is_dir() and default.is_dir(),
            "p0_default_board": board.is_file(),
            "p0_refresh_asset_api": True,  # /api/wall-asset in middleware
            "p0_prefs_stub": True,  # /api/wall-prefs stub
            "p0_shared_gutter": (components / "gutter.js").is_file(),
            "p0_shared_js_lib": (root / "lib" / "theme.css").is_file()
            and (root / "lib" / "popup.js").is_file(),
            "p0_domain_folders": all(
                (default / d / f"{d}.js").is_file() for d in ("mail", "score", "floor", "todo")
            ),
        },
        "parked_p1": {
            "live_in_browser_tweak": False,
            "desk_pack_save_load": False,
            "marketplace_private_public": False,
            "office_share_adopt": False,
        },
        "blockers_for_live_share": [
            "board.html still large - domain folders (cut 5) enable mail/score/floor override without whole-file fork",
            "no pack marketplace / adopt API yet (P1 parked)",
            "setOpen still duplicated for help boxes (gutter applyPct/onMove/onUp extracted cut 4)",
            "pure rules still embedded in HTML (this package starts the exit)",
        ],
        "ease_of_change_targets": [
            "keep pure rules in wall_logic (packs call; chrome stays tweakable)",
            "domain folders shipped (mail/, score/, floor/, todo/) - deepen extracts; wire DB knobs next",
            "marketplace adopt copies prefs - does not force-edit author's pack",
            "do not bake one office chrome into core agent_coord forever",
        ],
    }
