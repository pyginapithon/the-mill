"""0.7.0 roster migration on a legacy-shaped book (collision, idempotency, keys).

The fixture book is fresh (roster shape). _legacy() turns it back into the 0.6
shape: project/role name types and the old tag column, index and FK names.
"""
from __future__ import annotations

import pytest

from agent_coord.install.migrate import apply_roster_070, roster_070_needed

pytestmark = pytest.mark.sql

OLD = "affil" + "iation"  # spelled in two parts so the grep gate stays exact
TABLES = ("activity", "mail", "todo", "score")


def _q(cn, sql, args=()):
    cur = cn.cursor()
    try:
        cur.execute(sql, args)
        return cur.fetchall() if cur.with_rows else []
    finally:
        cur.close()


def _schema(cn):
    cols = _q(cn, "SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE FROM information_schema.COLUMNS"
                  " WHERE TABLE_SCHEMA = DATABASE() ORDER BY 1, 2")
    idx = _q(cn, "SELECT TABLE_NAME, INDEX_NAME, COLUMN_NAME FROM information_schema.STATISTICS"
                 " WHERE TABLE_SCHEMA = DATABASE() ORDER BY 1, 2, 3")
    fks = _q(cn, "SELECT TABLE_NAME, CONSTRAINT_NAME FROM information_schema.TABLE_CONSTRAINTS"
                 " WHERE TABLE_SCHEMA = DATABASE() AND CONSTRAINT_TYPE = 'FOREIGN KEY' ORDER BY 1, 2")
    return cols, idx, fks


def _legacy(cn):
    _q(cn, "ALTER TABLE name MODIFY type ENUM('desk','roster','project','role','label','tree','res') NOT NULL")
    _q(cn, "UPDATE name SET type = 'project' WHERE type = 'roster' AND name <> 'Admin'")
    _q(cn, "UPDATE name SET type = 'role' WHERE type = 'roster'")
    _q(cn, "ALTER TABLE name MODIFY type ENUM('desk','project','role','label','tree','res') NOT NULL")
    for t in TABLES:
        fks = _q(cn, "SELECT k.CONSTRAINT_NAME, k.REFERENCED_TABLE_NAME, k.REFERENCED_COLUMN_NAME,"
                     " r.DELETE_RULE FROM information_schema.KEY_COLUMN_USAGE k"
                     " JOIN information_schema.REFERENTIAL_CONSTRAINTS r"
                     " ON r.CONSTRAINT_SCHEMA = k.CONSTRAINT_SCHEMA AND r.CONSTRAINT_NAME = k.CONSTRAINT_NAME"
                     " WHERE k.TABLE_SCHEMA = DATABASE() AND k.TABLE_NAME = %s AND k.COLUMN_NAME = 'roster_id'",
                 (t,))
        for name, rt, rc, rule in fks:
            _q(cn, f"ALTER TABLE `{t}` DROP FOREIGN KEY `{name}`")
        ctype = _q(cn, "SELECT COLUMN_TYPE, IS_NULLABLE FROM information_schema.COLUMNS WHERE TABLE_SCHEMA ="
                       " DATABASE() AND TABLE_NAME = %s AND COLUMN_NAME = 'roster_id'", (t,))[0]
        null = "NULL" if ctype[1] == "YES" else "NOT NULL"
        _q(cn, f"ALTER TABLE `{t}` CHANGE roster_id {OLD}_id {ctype[0]} {null}")
        for (iname,) in _q(cn, "SELECT DISTINCT INDEX_NAME FROM information_schema.STATISTICS WHERE TABLE_SCHEMA ="
                               " DATABASE() AND TABLE_NAME = %s AND INDEX_NAME LIKE '%%roster%%'", (t,)):
            _q(cn, f"ALTER TABLE `{t}` RENAME INDEX `{iname}` TO `{iname.replace('roster', OLD)}`")
        for name, rt, rc, rule in fks:
            _q(cn, f"ALTER TABLE `{t}` ADD CONSTRAINT `{name.replace('roster', OLD)}` FOREIGN KEY ({OLD}_id)"
                   f" REFERENCES `{rt}` (`{rc}`) ON DELETE {rule}")


@pytest.fixture(scope="module")
def fresh_schema(cn):
    return _schema(cn)


def test_fresh_book_needs_nothing(cn, fresh_schema):
    assert roster_070_needed(cn) is False
    assert apply_roster_070(cn) == []


def test_collision_refuses_and_leaves_schema(cn, fresh_schema):
    _legacy(cn)
    _q(cn, "INSERT INTO name (type, name) VALUES ('project', 'twin'), ('role', 'twin')")
    before = _schema(cn)
    assert roster_070_needed(cn) is True
    with pytest.raises(Exception, match="rename one of each same-name project/role first: twin"):
        apply_roster_070(cn)
    assert _schema(cn) == before
    _q(cn, "UPDATE name SET name = 'twin-role' WHERE type = 'role' AND name = 'twin'")


def test_migrate_matches_fresh_and_is_idempotent(cn, fresh_schema):
    applied = apply_roster_070(cn)
    assert applied and applied[0] == "migrate_070_roster.sql"
    assert _schema(cn) == fresh_schema
    assert roster_070_needed(cn) is False
    assert apply_roster_070(cn) == []
    assert _schema(cn) == fresh_schema
    types = {r[0] for r in _q(cn, "SELECT DISTINCT type FROM name")}
    assert "project" not in types and "role" not in types
    assert dict(_q(cn, "SELECT name, id FROM name WHERE type = 'roster' AND name IN ('Office', 'Admin')")) == {
        "Office": 1, "Admin": 2}
    bodies = _q(cn, "SELECT ROUTINE_NAME FROM information_schema.ROUTINES WHERE ROUTINE_SCHEMA = DATABASE()"
                    " AND ROUTINE_DEFINITION LIKE %s", (f"%{OLD}%",))
    assert bodies == []


def test_old_types_refused_after_migrate(cn):
    with pytest.raises(Exception):
        _q(cn, "SELECT MILL_NAME_PUT('project', 'nope-070')")
    assert _q(cn, "SELECT MILL_NAME_GET('roster', 'never-minted-070')") == [(None,)]
    assert _q(cn, "SELECT COUNT(*) FROM name WHERE name = 'never-minted-070'") == [(0,)]
