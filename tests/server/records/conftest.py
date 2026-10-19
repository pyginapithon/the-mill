"""Shared SQL arrange helpers for throwaway SQL suites (#34 get/put gate).

mill_name_get is SELECT-only. Tests that need project/desk/role/label rows
must mint them via mill_name_put (get_or_insert / host_put / join upsert),
not rely on read/list side effects.
"""
from __future__ import annotations

import os

import pytest

from agent_coord.server.records import name as rec_name


def seed_names(cn, *specs: tuple[str, str]) -> list[int]:
    """Intentional create via mill_name_put. Idempotent. Skips blanks.

    Each spec is (stored name, kind). The name is stored as given.
    """
    out: list[int] = []
    for spec in specs:
        name, kind = spec
        s = (name or "").strip()
        if not s:
            continue
        out.append(rec_name.get_or_insert(cn, s, kind))
    return out


@pytest.fixture(scope="module")
def cn(request):
    """One wiped book per test module.

    Two modules in one process must not share a book. A read cursor left by
    test_room_reply would hide the branch on the next file.
    """
    import mysql.connector

    from agent_coord.server.records import apply, connect
    from agent_coord.server.records.db import conn_kwargs
    from tests.sql_isolate import throwaway_db

    mod = request.module.__name__.rsplit(".", 1)[-1]
    test_db = throwaway_db("mill_" + mod)
    # connect() returns the process pool when the name matches the env book.
    # That pool stays on the first schema, and wipe.sql does not drop tree_read,
    # so the next module's mail ids restart on top of a stale read cursor.
    saved = os.environ.pop("AGENT_COORD_DATABASE", None)
    try:
        kw = conn_kwargs()
        kw.pop("database", None)
        kw["autocommit"] = True
        admin = mysql.connector.connect(**kw)
        cur = admin.cursor()
        cur.execute(
            f"CREATE DATABASE IF NOT EXISTS `{test_db}` "
            "DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_0900_ai_ci"
        )
        cur.close()
        admin.close()
        c = connect(test_db)
        apply(c, wipe=True)
    except Exception as e:
        if saved is not None:
            os.environ["AGENT_COORD_DATABASE"] = saved
        pytest.skip(f"mysql mill records: {e}")
    try:
        yield c
    finally:
        c.close()
        if saved is None:
            os.environ.pop("AGENT_COORD_DATABASE", None)
        else:
            os.environ["AGENT_COORD_DATABASE"] = saved
