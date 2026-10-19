"""#186 peek edges that need a book: a deleted id, and an id in another project."""
from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.sql

from agent_coord.helpers.errors import CoordError
from agent_coord.server.api.mill import rpc
from agent_coord.server.records import apply, connect, todo
from agent_coord.server.records.db import conn_kwargs as _conn_kwargs
from tests.server.records.conftest import seed_names
from tests.server.records.test_probe_delete import _Book, _probe
from tests.sql_isolate import throwaway_db

TEST_DB = throwaway_db("mill_peek_186")
FIX = "t-0a1b2c3d"


def _cn():
    import mysql.connector

    kw = _conn_kwargs()
    kw.pop("database", None)
    kw["autocommit"] = True
    admin = mysql.connector.connect(**kw)
    cur = admin.cursor()
    cur.execute(
        f"CREATE DATABASE IF NOT EXISTS `{TEST_DB}` "
        "DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_0900_ai_ci"
    )
    cur.close()
    admin.close()
    os.environ["AGENT_COORD_DATABASE"] = TEST_DB
    cn = connect(TEST_DB)
    apply(cn, wipe=True)
    return cn


@pytest.fixture(scope="module")
def cn():
    try:
        c = _cn()
    except Exception as e:
        pytest.skip(f"mysql mill records: {e}")
    seed_names(
        c,
        ("pk_real", "roster"),
        (FIX, "roster"),
        ("pk_me", "desk"),
    )
    yield c
    c.close()


def test_deleted_id_names_the_card(cn) -> None:
    tid = int(todo.insert(cn, FIX, "pk_me", "open", todo.pack({"slug": "pk-gone"}))[0]["id"])
    _probe(cn, "pk_me", "todo", tid)
    with pytest.raises(CoordError, match=r"todo: no card %s in pk_real; it is deleted" % tid):
        rpc._h_todo(_Book(cn), {"need": str(tid)}, "pk_real", "pk_me")


def test_id_in_another_project_refuses(cn) -> None:
    tid = int(todo.insert(cn, FIX, "pk_me", "open", todo.pack({"slug": "pk-other"}))[0]["id"])
    with pytest.raises(CoordError, match=r"todo: no card %s in pk_real" % tid):
        rpc._h_todo(_Book(cn), {"need": str(tid), "fixtures": True}, "pk_real", "pk_me")
    got = rpc._h_todo(_Book(cn), {"need": str(tid), "fixtures": True}, FIX, "pk_me")
    assert [int(r["id"]) for r in got] == [tid]
