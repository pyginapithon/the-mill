"""F20: a room read reads the room once and checks participation with EXISTS."""
from __future__ import annotations

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.sql

from agent_coord.helpers.errors import CoordError
from agent_coord.server.admin.guard import is_role_admin
from agent_coord.server.api.mill import rpc
from agent_coord.server.records import mail as rec_mail
from agent_coord.server.records import member as rec_member
from agent_coord.server.records import tree as rec_tree
from tests.server.records.conftest import seed_names


class _Book:
    def __init__(self, cn):
        self._cn = cn


@pytest.fixture(scope="module")
def room(cn):
    seed_names(cn, ("ro", "roster"), ("ro_a", "desk"), ("ro_b", "desk"), ("ro_c", "desk"),
               ("ro_late", "desk"), ("ro_out", "desk"))
    book = _Book(cn)
    root = int(rpc._h_send(book, {"src": "ro_a", "dst": "ro_b", "body": "root", "name": "f20-room"}, "ro", "ro_a")["id"])
    r1 = int(rpc._h_reply(book, {"mail_id": root, "body": "r1", "src": "ro_b"}, "ro", "ro_b")["id"])
    r2 = int(rpc._h_reply(book, {"mail_id": r1, "body": "r2", "src": "ro_a", "mail_tos": ["ro_c"]}, "ro", "ro_a")["id"])
    r3 = int(rpc._h_reply(book, {"mail_id": r2, "body": "r3", "src": "ro_c"}, "ro", "ro_c")["id"])
    side = int(rpc._h_reply(book, {"mail_id": root, "body": "side", "src": "ro_late"}, "ro", "ro_late")["id"])
    off = int(rpc._h_send(book, {"src": "ro_a", "dst": "ro_b", "body": "plain"}, "ro", "ro_a")["id"])
    return {"book": book, "ids": [root, r1, r2, r3, side], "off": off}


def test_participant_exists_matches_the_full_cast(cn, room):
    for mid in room["ids"] + [room["off"]]:
        cast = rec_mail.room_participants(cn, mid)
        for who in ("ro_a", "ro_b", "ro_c", "ro_late", "ro_out", "nobody-here", ""):
            assert rec_mail.room_participant(cn, mid, who) == (bool(who) and who in cast), (mid, who)
    # a recipient-only desk of an off-tree letter, and its outsider
    assert rec_mail.room_participant(cn, room["off"], "ro_b")
    assert not rec_mail.room_participant(cn, room["off"], "ro_c")


def test_one_tree_read_gives_the_same_crumbs_nodes_and_tree_id(cn, room):
    for mid in room["ids"]:
        r = rec_mail.RoomRead(cn, mid)
        assert r.crumbs == rec_mail.tree_crumbs(cn, mid)
        assert r.nodes == rec_mail.room_mail_nodes(cn, mid)
        assert r.tree_id == rec_mail.room_tree_id(cn, mid)
        assert r.crumbs_for(cn, room["ids"]) == rec_mail.tree_crumbs_batch(cn, room["ids"])
    off = rec_mail.RoomRead(cn, room["off"])
    assert off.nodes == [] and off.crumbs == {} and off.tree_id is None and off.ids() == [room["off"]]


def test_crumbs_skip_a_card_on_the_same_tree(cn, room):
    from agent_coord.server.records import todo

    tid = int(todo.insert(cn, "ro", "ro_a", "open", "card under a letter")[0]["id"])
    tree_name = rec_mail.tree_crumbs(cn, room["ids"][2])["tree"]
    rec_tree.add(cn, "mail", room["ids"][2], "todo", tid, tree_name)
    r = rec_mail.RoomRead(cn, room["ids"][3])
    assert r.crumbs_for(cn, room["ids"]) == rec_mail.tree_crumbs_batch(cn, room["ids"])
    assert sorted(n["id"] for n in r.nodes) == sorted(room["ids"])  # the card is not a letter node


def test_mail_thread_reads_the_tree_once(cn, room):
    real = rec_tree.select
    calls = []

    def counting(c, name):
        calls.append(name)
        return real(c, name)

    with patch.object(rec_tree, "select", side_effect=counting):
        got = rpc._h_mail_thread(room["book"], {"scope": "room", "mail_id": room["ids"][3]}, "ro", "ro_c")
    assert got["chain"]
    assert len(calls) == 1


def test_outsider_refusal_text_unchanged(cn, room):
    with pytest.raises(CoordError) as ei:
        rpc._h_mail_thread(room["book"], {"scope": "room", "mail_id": room["ids"][3]}, "ro", "ro_out")
    assert str(ei.value) == (
        "mail-thread: not a participant in this room; "
        f"run mill reply {room['ids'][0]} <body> to join, "
        "or ask a participant to mill add you at a letter of it"
    )


def test_admin_exists(cn, room):
    rec_member.put(cn, "Admin", "ro_a")
    assert is_role_admin(cn, "ro_a")
    assert not is_role_admin(cn, "ro_b")
    assert not is_role_admin(cn, "")
    assert not is_role_admin(cn, "Admin")
    got = rpc._h_mail_thread(room["book"], {"scope": "room", "mail_id": room["ids"][3]}, "ro", "ro_a")
    assert {int(m["id"]) for m in got["chain"]} == set(room["ids"])
    rec_member.delete(cn, "Admin", "ro_a")
    assert not is_role_admin(cn, "ro_a")
