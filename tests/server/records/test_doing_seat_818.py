"""#818 on a real book: join becomes doing, the seat splits off. Row F117 (doing-schema).

(a) the migration keeps every join id, and every activity, watcher and label
    row that pointed at a join now resolves as doing;
(b) the seat holds the per-desk state and connect, socket, wake and reset
    behave as before;
(c) mill doing appends a new entry, it never overwrites;
(d) the migration is idempotent (a second ensure changes nothing).

The pre-818 book is built on a wiped tip book: drop seat and doing, put the
old type lists back, create the old `join` table and fill it.
"""
from __future__ import annotations

import pytest

from agent_coord.client.tokens import token_hash
from agent_coord.install import migrate
from agent_coord.server.records import join as rec_join
from agent_coord.server.records.db import call, rows_done, scalar_done
from tests.server.records.conftest import seed_names

pytestmark = pytest.mark.sql

OLD5 = "ENUM('mail','todo','join','hold','score')"
TYPE_TABLES = ("activity", "label", "tree", "mail", "mail_to", "todo", "hold", "score")

OLD_JOIN = (
    "CREATE TABLE `join` ("
    " type ENUM('mail','todo','join','hold','score') NOT NULL DEFAULT 'join',"
    " id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,"
    " created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),"
    " updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),"
    " desk_id BIGINT UNSIGNED NOT NULL,"
    " token_hash CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NULL,"
    " doing VARCHAR(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT '',"
    " delivery_mode ENUM('websocket','webhook','polling') NOT NULL DEFAULT 'polling',"
    " endpoint_url VARCHAR(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL,"
    " endpoint_key VARCHAR(512) CHARACTER SET ascii COLLATE ascii_bin NULL,"
    " wake_on ENUM('all','addressed') NOT NULL DEFAULT 'all',"
    " lan_ip VARCHAR(45) CHARACTER SET ascii COLLATE ascii_bin NULL,"
    " time_connect DATETIME(6) NULL,"
    " time_disconnect DATETIME(6) NULL,"
    " PRIMARY KEY (type, id), UNIQUE KEY idx_id (id), UNIQUE KEY idx_desk (desk_id),"
    " KEY idx_lan_updated (lan_ip, updated), KEY idx_token_hash (token_hash),"
    " CONSTRAINT fk_join_desk FOREIGN KEY (desk_id) REFERENCES name (id) ON DELETE RESTRICT"
    ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci"
)

# Old rows: (desk, id, doing, token, delivery, url, key, wake_on, lan, connected)
OLD_ROWS = (
    ("fx818-a", 7, "reading letter 2516 | tests running", "tok-a", "webhook",
     "https://hooks.example.test/fx818-a", "fx818-key-a", "addressed", "192.0.2.7", True),
    ("fx818-b", 11, "present", None, "websocket", None, None, "all", None, False),
    ("fx818-c", 12, "", "tok-c", "polling", None, None, "all", "192.0.2.12", True),
)


def _x(cn, sql: str, args: tuple = ()) -> None:
    cur = cn.cursor()
    try:
        cur.execute(sql, args)
    finally:
        cur.close()


def _ctype(cn, table: str) -> str:
    return str(scalar_done(
        cn,
        "SELECT COLUMN_TYPE FROM information_schema.COLUMNS"
        " WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND COLUMN_NAME = 'type'",
        (table,),
    ) or "")


def _has_table(cn, table: str) -> bool:
    return bool(scalar_done(
        cn,
        "SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s",
        (table,),
    ))


def _desk_id(cn, desk: str) -> int:
    return int(scalar_done(cn, "SELECT id FROM name WHERE type = 'desk' AND name = %s", (desk,)))


def _old_book(cn) -> dict:
    """Turn the wiped tip book into a pre-818 book with three seats."""
    seed_names(cn, ("fx818", "roster"), ("fx818-lbl", "label"),
               *[(r[0], "desk") for r in OLD_ROWS])
    _x(cn, "SET FOREIGN_KEY_CHECKS = 0")
    try:
        _x(cn, "DROP TRIGGER IF EXISTS doing_no_delete_in_tree")
        _x(cn, "DROP TABLE IF EXISTS doing")
        _x(cn, "DROP TABLE IF EXISTS seat")
        for t in TYPE_TABLES:
            dflt = {"mail": " DEFAULT 'mail'", "mail_to": " DEFAULT 'mail'", "todo": " DEFAULT 'todo'",
                    "hold": " DEFAULT 'hold'", "score": " DEFAULT 'score'"}.get(t, "")
            _x(cn, f"ALTER TABLE `{t}` MODIFY type {OLD5} NOT NULL{dflt}")
        # A drifted watcher list, as on the cloud book: an older pack's 'name' value stays.
        _x(cn, "ALTER TABLE watcher MODIFY type ENUM('todo','join','hold','score','name') NOT NULL")
        _x(cn, OLD_JOIN)
    finally:
        _x(cn, "SET FOREIGN_KEY_CHECKS = 1")
    for desk, jid, doing, tok, mode, url, key, wake_on, lan, up in OLD_ROWS:
        did = _desk_id(cn, desk)
        _x(cn,
           "INSERT INTO `join` (id, desk_id, token_hash, doing, delivery_mode, endpoint_url,"
           " endpoint_key, wake_on, lan_ip, time_connect, time_disconnect)"
           " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,"
           " IF(%s, NOW(6), NULL), IF(%s, NULL, NOW(6)))",
           (jid, did, token_hash(tok) if tok else None, doing, mode, url, key, wake_on, lan, up, up))
        _x(cn, "INSERT INTO activity (type, id, desk_id, roster_id) VALUES ('join', %s, %s, 1)", (jid, did))
        _x(cn, "INSERT INTO watcher (type, id, desk_id) VALUES ('join', %s, %s)", (jid, did))
    lbl = int(scalar_done(cn, "SELECT id FROM name WHERE type = 'label' AND name = 'fx818-lbl'"))
    _x(cn, "INSERT INTO label (type, id, name_id) VALUES ('join', 7, %s)", (lbl,))
    _x(cn, "INSERT INTO watcher (type, id, desk_id) VALUES ('name', 1, %s)", (_desk_id(cn, "fx818-b"),))
    cn.commit()
    return {r[0]: rows_done(cn, "SELECT * FROM `join` WHERE id = %s", (r[1],))[0] for r in OLD_ROWS}


@pytest.fixture(scope="module")
def migrated(cn):
    before = _old_book(cn)
    assert migrate.doing_818_needed(cn)
    first = migrate.ensure(cn)
    return {"before": before, "first": first}


def test_a_ids_and_pointers_resolve_as_doing(cn, migrated):
    assert "migrate_818_doing.sql" in migrated["first"]["applied"]
    assert not _has_table(cn, "join")
    rows = {int(r["id"]): r for r in rows_done(cn, "SELECT * FROM doing ORDER BY id")}
    for desk, jid, doing, *_ in OLD_ROWS:
        got = rows[jid]
        assert got["type"] == "doing"
        assert got["desk_id"] == _desk_id(cn, desk)
        assert got["text"] == doing
        assert got["on_type"] is None and got["on_id"] is None
        assert got["waiting_type"] is None and got["waiting_id"] is None
    for table in ("activity", "watcher", "label"):
        assert scalar_done(cn, f"SELECT COUNT(*) FROM `{table}` WHERE type = 'join'") == 0
        dangling = scalar_done(
            cn,
            f"SELECT COUNT(*) FROM `{table}` x WHERE x.type = 'doing'"
            " AND NOT EXISTS (SELECT 1 FROM doing d WHERE d.id = x.id)",
        )
        assert dangling == 0, table
    assert scalar_done(cn, "SELECT COUNT(*) FROM activity WHERE type = 'doing'") == 3
    assert scalar_done(cn, "SELECT COUNT(*) FROM watcher WHERE type = 'doing'") == 3
    assert scalar_done(cn, "SELECT COUNT(*) FROM label WHERE type = 'doing' AND id = 7") == 1
    # The drifted watcher value keeps its row.
    assert scalar_done(cn, "SELECT COUNT(*) FROM watcher WHERE type = 'name'") == 1
    for t in TYPE_TABLES + ("doing",):
        assert _ctype(cn, t) == "enum('mail','todo','doing','hold','score')", t
    assert _ctype(cn, "watcher") == "enum('todo','doing','hold','score','name')"
    # label/tree/mail_to keep their FKs on (type, id).
    fks = {r["CONSTRAINT_NAME"] for r in rows_done(
        cn,
        "SELECT CONSTRAINT_NAME FROM information_schema.TABLE_CONSTRAINTS"
        " WHERE TABLE_SCHEMA = DATABASE() AND CONSTRAINT_TYPE = 'FOREIGN KEY'")}
    assert {"fk_label_activity", "fk_tree_activity", "fk_mail_to_mail",
            "fk_seat_desk", "fk_doing_desk", "fk_doing_roster"} <= fks


def test_b_seat_holds_state_and_behaves(cn, migrated):
    cols = {r["COLUMN_NAME"] for r in rows_done(
        cn,
        "SELECT COLUMN_NAME FROM information_schema.COLUMNS"
        " WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'seat'")}
    assert "type" not in cols  # not an activity
    assert not {"token_hash", "endpoint_key", "lan_ip", "updated"} & {
        r["COLUMN_NAME"] for r in rows_done(
            cn,
            "SELECT COLUMN_NAME FROM information_schema.COLUMNS"
            " WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'doing'")}
    for desk, jid, *_ in OLD_ROWS:
        old = migrated["before"][desk]
        seat = rows_done(cn, "SELECT * FROM seat WHERE desk_id = %s", (_desk_id(cn, desk),))
        assert len(seat) == 1
        for k in ("token_hash", "delivery_mode", "endpoint_url", "endpoint_key", "wake_on",
                  "lan_ip", "time_connect", "time_disconnect", "created", "updated"):
            assert seat[0][k] == old[k], (desk, k)
    # Same behavior as before through the procedures.
    assert rec_join.token_matches(cn, "fx818-a", token_hash("tok-a"))
    assert rec_join.desk_for_token_hash(cn, token_hash("tok-c")) == "fx818-c"
    assert rec_join.wake_state(cn, "fx818-a") == {
        "armed": True, "host": "hooks.example.test", "wake_on": "addressed"}
    assert rec_join.wake_target(cn, "fx818-a") == ("https://hooks.example.test/fx818-a", "fx818-key-a")
    rec_join.mark_socket(cn, "fx818-b", up=True)
    seat_b = rows_done(cn, "SELECT time_connect, time_disconnect FROM seat WHERE desk_id = %s",
                       (_desk_id(cn, "fx818-b"),))[0]
    assert seat_b["time_connect"] is not None and seat_b["time_disconnect"] is None
    got = call(cn, "mill_join_connect", ["fx818-b"])[0]
    assert int(got["id"]) == 11  # the bump lands on the desk's current entry
    rec_join.set_lan_ip(cn, "fx818-b", "192.0.2.11")
    assert scalar_done(cn, "SELECT lan_ip FROM seat WHERE desk_id = %s", (_desk_id(cn, "fx818-b"),)) == "192.0.2.11"
    rec_join.wake_off(cn, "fx818-a")
    assert rec_join.wake_target(cn, "fx818-a") is None
    rec_join.reset(cn, "fx818", "fx818-c")
    assert rec_join.token_hash_for_desk(cn, "fx818-c") == ""
    sel = {r["desk"]: r for r in rec_join.select(cn, "")}
    assert sel["fx818-c"]["doing"] == ""
    assert sel["fx818-b"]["type"] == "doing" and sel["fx818-b"]["doing"] == "present"
    # A bump command writes no new entry.
    n = scalar_done(cn, "SELECT COUNT(*) FROM doing")
    rec_join.touch(cn, "fx818", "fx818-b")
    assert scalar_done(cn, "SELECT COUNT(*) FROM doing") == n


def test_c_doing_appends(cn, migrated):
    did = _desk_id(cn, "fx818-a")
    before = rows_done(cn, "SELECT id, text FROM doing WHERE desk_id = %s ORDER BY id", (did,))
    one = rec_join.push_doing(cn, "fx818", "fx818-a", "pr open, waiting on ci")
    two = rec_join.push_doing(cn, "fx818", "fx818-a", "done")
    after = rows_done(cn, "SELECT id, text FROM doing WHERE desk_id = %s ORDER BY id", (did,))
    assert after[: len(before)] == before  # nothing overwritten
    assert [r["text"] for r in after[len(before):]] == ["pr open, waiting on ci", "done"]
    assert int(one[0]["id"]) < int(two[0]["id"])
    assert two[0]["doing"] == "done"
    for r in after[len(before):]:
        assert scalar_done(cn, "SELECT COUNT(*) FROM activity WHERE type = 'doing' AND id = %s", (r["id"],)) == 1
    sel = {r["desk"]: r for r in rec_join.select(cn, "")}
    assert sel["fx818-a"]["doing"] == "done"
    assert int(sel["fx818-a"]["id"]) == int(two[0]["id"])


def test_d_migration_is_idempotent(cn, migrated):
    snap = lambda: {
        t: scalar_done(cn, f"SELECT COUNT(*) FROM `{t}`")
        for t in ("activity", "watcher", "label", "seat", "doing")
    }
    types = {t: _ctype(cn, t) for t in TYPE_TABLES + ("doing", "watcher")}
    was = snap()
    assert not migrate.doing_818_needed(cn)
    second = migrate.ensure(cn)
    assert "migrate_818_doing.sql" not in second["applied"]
    assert migrate.apply_doing_818(cn) == []
    assert snap() == was
    assert {t: _ctype(cn, t) for t in TYPE_TABLES + ("doing", "watcher")} == types
    # run the file again by hand on a migrated book: nothing changes either.
    cur = cn.cursor()
    try:
        for stmt in migrate.split_script((migrate.sql_dir() / migrate.DOING_818).read_text(encoding="utf-8")):
            cur.execute(stmt)
        cn.commit()
    finally:
        cur.close()
    assert snap() == was
    assert {t: _ctype(cn, t) for t in TYPE_TABLES + ("doing", "watcher")} == types
