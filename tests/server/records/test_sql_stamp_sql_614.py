"""#614 on a real book: the wall knows when the book's SQL is not this pack's. Regression row F66 (sql-stamp).

Seen live: a pack update plus a wall restart left the stored procedures of
the previous pack; the wall served new code over them with health green.
"""
from __future__ import annotations

import pytest

from agent_coord.install import migrate

pytestmark = pytest.mark.sql

FIX = "mill install sql --apply"


def test_ensure_stamps_this_pack(cn):
    migrate.ensure(cn)
    st = migrate.sql_state(cn)
    assert st["ok"] is True
    assert st["book"] == st["pack"] == migrate.sql_digest()[:12]


def test_a_book_left_by_another_pack_is_stale(cn):
    migrate.ensure(cn)
    migrate._stamp_sql(cn, "0" * 64)
    st = migrate.sql_state(cn)
    assert st["ok"] is False
    assert st["book"] == "0" * 12
    assert st["fix"] == FIX


def test_a_book_from_before_the_stamp_is_stale(cn):
    migrate.ensure(cn)
    cur = cn.cursor()
    cur.execute("DROP FUNCTION IF EXISTS MILL_SQL_STAMP")
    cur.close()
    st = migrate.sql_state(cn)
    assert st["ok"] is False
    assert st["book"] == ""
    assert st["fix"] == FIX


def test_install_sql_apply_runs_ensure_and_verifies(cn):
    migrate._stamp_sql(cn, "0" * 64)
    out = migrate.install_sql(cn, apply=False)
    assert out["ok"] is False and out["applied"] is False and out["fix"] == FIX
    assert migrate.sql_state(cn)["ok"] is False
    out = migrate.install_sql(cn, apply=True)
    assert out["ok"] is True and out["applied"] is True
    assert migrate.sql_state(cn)["ok"] is True
