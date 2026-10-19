"""Domain folders under default pack (fungible cut 5)."""
from __future__ import annotations

import re

from agent_coord.web.wall_logic.domains import (
    BOARD_EQUIVALENT_MARKER,
    DOMAIN_IDS,
    domain_paths,
    domain_script_src,
    domains_contract,
)
from agent_coord.web.wall_logic.packs import default_board_path, pack_seam_inventory


def test_domain_folders_and_js_exist():
    paths = domain_paths()
    for d in DOMAIN_IDS:
        assert paths[d]["dir"].is_dir(), d
        js = paths[d]["js"]
        assert js.is_file(), js
        text = js.read_text(encoding="utf-8")
        assert f"WALL_UI_DEFAULT_{d.upper()}" in text
        assert "function" in text or "=>" in text


def test_domains_contract_and_board_wire():
    c = domains_contract()
    assert c["marker"] == BOARD_EQUIVALENT_MARKER
    assert c["path"] == "A"
    assert c["domains"] == list(DOMAIN_IDS)
    assert all(all(v.values()) for v in c["paths_exist"].values())
    board = default_board_path().read_text(encoding="utf-8")
    assert "WALL_UI_DEFAULT_DOMAINS" in board or "WALL_UI_DEFAULT_MAIL" in board
    for d in DOMAIN_IDS:
        src = domain_script_src(d)
        assert re.search(
            rf'src=[\"\']{re.escape(src)}(?:\?[^\"\']*)?[\"\']', board
        ), src
        js = (domain_paths()[d]["js"]).read_text(encoding="utf-8")
        assert f"WALL_UI_DEFAULT_{d.upper()}" in js
    # pure helpers come from modules (board may keep thin paint)
    assert "WallMail" in board or "mail/mail.js" in board
    inv = pack_seam_inventory()
    assert inv["shipped"].get("p0_domain_folders") is True


def test_domain_js_exports_expected_globals():
    mail = domain_paths()["mail"]["js"].read_text(encoding="utf-8")
    for name in ("mailDst", "mailIsBareHumanMailbox", "mailRowsForListDst", "WallMail"):
        assert name in mail
    score = domain_paths()["score"]["js"].read_text(encoding="utf-8")
    for name in ("numish", "kpiMiss", "scoreDeskRows", "WallScore"):
        assert name in score
    floor = domain_paths()["floor"]["js"].read_text(encoding="utf-8")
    for name in ("floorLayout", "floorEnsurePaintContract", "WallFloor"):
        assert name in floor
    todo = domain_paths()["todo"]["js"].read_text(encoding="utf-8")
    for name in ("millTodoCards", "isMillNeedId", "WallTodo"):
        assert name in todo
