"""The live-book SQL checker sees the pack routines and skips the files a live update must not reapply."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_SPEC = importlib.util.spec_from_file_location("check_sql", ROOT / "tools" / "check_sql.py")
assert _SPEC is not None and _SPEC.loader is not None
check_sql = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(check_sql)


def test_pack_routines_skip_wipe_and_tables():
    sql = ROOT / "agent_coord" / "server" / "sql"
    names = check_sql.pack_routines(sql)
    assert "MILL_NOW" in names
    assert "mill_now" not in names
    assert "mill_mail_insert" in names
    assert "mill_mail_open" in names
    assert "mill_human_open" in names
    assert "mill_human_put" in names
    assert "mill_human_roles" in names
    assert "mill_push_put" in names
    assert "mill_push_take" in names
    assert names == list(dict.fromkeys(names))


def test_skip_list_matches_the_live_update_rule():
    assert check_sql.SKIP == frozenset({"wipe.sql", "tables.sql"})
    order = (ROOT / "agent_coord" / "server" / "sql" / "apply_order.txt").read_text(encoding="utf-8")
    for name in check_sql.SKIP:
        assert name in order
