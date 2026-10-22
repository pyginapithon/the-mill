"""#221: an outsider trail of a mail names the room and how to join."""
from __future__ import annotations

import os
import uuid

import pytest

pytestmark = pytest.mark.sql

from agent_coord.helpers.errors import CoordError
from agent_coord.server.api.mill import rpc
from agent_coord.server.records import apply, connect
from agent_coord.server.records.db import conn_kwargs as _conn_kwargs
from tests.server.records.conftest import seed_names
from tests.sql_isolate import throwaway_db

TEST_DB = throwaway_db("mill_trail_221")


class _Book:
    def __init__(self, cn):
        self._cn = cn


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
    seed_names(c, ("unit", "roster"), ("asker", "desk"), ("tester", "desk"), ("outsider", "desk"))
    yield c
    c.close()


@pytest.fixture(autouse=True)
def _no_live_ws(monkeypatch):
    monkeypatch.setattr("agent_coord.server.api.mill.rpc._require_live_ws", lambda owner: None)


def _room(cn):
    book = _Book(cn)
    room = "ux-" + uuid.uuid4().hex[:6]
    root = rpc._h_send(
        book,
        {"src": "asker", "dst": "tester", "body": "room root", "name": room},
        "unit",
        "asker",
    )
    rid = int(root["id"])
    finding = rpc._h_reply(book, {"mail_id": rid, "body": "verb: trail"}, "unit", "asker")
    fid = int(finding["id"])
    card = rpc._h_open(
        book,
        {
            "need": f"f{fid}-try-" + uuid.uuid4().hex[:6],
            "detail": "one try",
            "parent_type": "mail",
            "parent_id": fid,
        },
        "unit",
        "asker",
    )
    return book, rid, fid, int(card["id"])


def test_outsider_mail_names_the_room_and_the_join(cn) -> None:
    book, rid, fid, _card = _room(cn)
    with pytest.raises(CoordError) as ei:
        rpc._h_trail(book, {"node": f"mail:{fid}"}, "unit", "outsider")
    msg = str(ei.value)
    assert "not a participant" in msg
    assert f"mill reply {rid} --body-file PATH to join" in msg
    assert "<body>" not in msg
    assert "mill add" in msg
    assert "sender or recipient" not in msg


def test_outsider_plain_letter_is_private_no_open_join(cn) -> None:
    # #sec S-3: a plain (off-tree) letter is private; it has no reply-to-join.
    # The refusal names it private and points at mill add, not mill reply.
    book = _Book(cn)
    sent = rpc._h_send(book, {"src": "asker", "dst": "tester", "body": "plain"}, "unit", "asker")
    mid = int(sent["id"])
    with pytest.raises(CoordError) as ei:
        rpc._h_trail(book, {"node": f"mail:{mid}"}, "unit", "outsider")
    msg = str(ei.value)
    assert f"mail {mid} is private" in msg
    assert "mill add" in msg
    assert f"mill reply {mid}" not in msg


def test_participant_mail_trail_still_reads(cn) -> None:
    book, rid, fid, card = _room(cn)
    out = rpc._h_trail(book, {"node": f"mail:{fid}"}, "unit", "tester")
    ids = [(n["kind"], n["id"]) for n in out["nodes"]]
    assert ("mail", fid) in ids
    assert ("todo", card) in ids
    root = rpc._h_trail(book, {"node": f"mail:{rid}"}, "unit", "asker")
    assert ("mail", rid) in [(n["kind"], n["id"]) for n in root["nodes"]]


def test_outsider_todo_trail_still_reads(cn) -> None:
    book, _rid, _fid, card = _room(cn)
    out = rpc._h_trail(book, {"node": f"todo:{card}"}, "unit", "outsider")
    assert [(n["kind"], n["id"]) for n in out["nodes"]][0] == ("todo", card)


def test_hold_id_is_not_a_trail_target(cn) -> None:
    book = _Book(cn)
    held = rpc._h_hold(book, {"resource": "docs/a.md"}, "unit", "asker")
    hid = int(held["id"])
    with pytest.raises(CoordError) as ei:
        rpc._h_trail(book, {"node": f"hold:{hid}"}, "unit", "outsider")
    assert "mail id or todo id" in str(ei.value)
