# -*- coding: utf-8 -*-
"""Security: who may join a letter and who may change who else is on it (#sec S-3).

Collaboration by default (#672): every desk in the office reads every letter, so
any desk may join any letter itself, by `reply` or by `add mail:ID` (itself).
Changing ANOTHER desk's place on a letter (`add`/`remove mail:ID OTHER`) still
needs the caller to be the sender, a recipient, a participant of its room, or
Admin.
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.sql

from agent_coord.helpers.errors import CoordError
from agent_coord.server.api.mill import rpc
from agent_coord.server.records import mail as rec_mail
from agent_coord.server.records import tree as rec_tree
from tests.server.records.conftest import seed_names


class _Book:
    def __init__(self, cn):
        self._cn = cn


@pytest.fixture(autouse=True)
def _no_live_ws(monkeypatch):
    monkeypatch.setattr(
        "agent_coord.server.api.mill.rpc._require_live_ws", lambda owner: None
    )


def _seed(cn):
    seed_names(
        cn,
        ("unit", "roster"),
        ("sa_sender", "desk"),
        ("sa_recip", "desk"),
        ("sa_outsider", "desk"),
        ("sa_third", "desk"),
    )


def _desks(cn, mid):
    return {str(r.get("desk") or "") for r in rec_mail.to_list(cn, int(mid))}


# --- #672: any desk may join any letter itself ---

def test_outsider_can_add_self_to_direct_letter(cn):
    _seed(cn)
    book = _Book(cn)
    sent = rpc._h_send(
        book, {"src": "sa_sender", "dst": "sa_recip", "body": "direct"}, "unit", "sa_sender"
    )
    mid = int(sent["id"])
    out = rpc._h_add_remove(
        book, {"verb": "add", "type": "mail", "id": mid}, "unit", "sa_outsider"
    )
    assert out["ok"] is True
    assert "sa_outsider" in _desks(cn, mid)


def test_outsider_can_reply_to_direct_letter(cn):
    _seed(cn)
    book = _Book(cn)
    sent = rpc._h_send(
        book, {"src": "sa_sender", "dst": "sa_recip", "body": "direct2"}, "unit", "sa_sender"
    )
    mid = int(sent["id"])
    rep = rpc._h_reply(book, {"mail_id": mid, "body": "me too"}, "unit", "sa_outsider")
    assert int(rep["id"]) > mid
    # the reply joins visibly: it is a letter from the replying desk
    letter = rec_mail.letter_row(cn, int(rep["id"]))
    assert str(letter.get("desk") or "") == "sa_outsider"
    assert "sa_outsider" in rec_mail.room_participants(cn, mid)


# --- edge/regression: legitimate participants keep working ---

def test_recipient_can_add_another_to_their_letter(cn):
    _seed(cn)
    book = _Book(cn)
    sent = rpc._h_send(
        book, {"src": "sa_sender", "dst": "sa_recip", "body": "hi"}, "unit", "sa_sender"
    )
    mid = int(sent["id"])
    out = rpc._h_add_remove(
        book,
        {"verb": "add", "type": "mail", "id": mid, "who": "sa_third"},
        "unit",
        "sa_recip",
    )
    assert out["ok"] is True
    assert "sa_third" in _desks(cn, mid)


def test_sender_can_reply_to_own_private_letter_opening_room(cn):
    _seed(cn)
    book = _Book(cn)
    sent = rpc._h_send(
        book, {"src": "sa_sender", "dst": "sa_recip", "body": "root"}, "unit", "sa_sender"
    )
    mid = int(sent["id"])
    rep = rpc._h_reply(book, {"mail_id": mid, "body": "follow up"}, "unit", "sa_sender")
    assert int(rep["id"]) > mid
    assert rec_tree.on_tree(cn, "mail", mid)


def test_recipient_can_reply_to_private_letter_opening_room(cn):
    _seed(cn)
    book = _Book(cn)
    sent = rpc._h_send(
        book, {"src": "sa_sender", "dst": "sa_recip", "body": "root2"}, "unit", "sa_sender"
    )
    mid = int(sent["id"])
    rep = rpc._h_reply(book, {"mail_id": mid, "body": "got it"}, "unit", "sa_recip")
    assert int(rep["id"]) > mid


def test_nonmember_reply_into_existing_room_still_joins(cn):
    _seed(cn)
    book = _Book(cn)
    root = rpc._h_send(
        book,
        {"src": "sa_sender", "dst": "sa_recip", "body": "room root", "name": "sa-room"},
        "unit",
        "sa_sender",
    )
    rid = int(root["id"])
    assert rec_tree.on_tree(cn, "mail", rid)
    rep = rpc._h_reply(book, {"mail_id": rid, "body": "joining in"}, "unit", "sa_outsider")
    assert int(rep["id"]) > rid


def test_nonmember_adds_self_to_room_but_not_another(cn):
    # #672: a desk joins a room visibly without posting; it still cannot put
    # another desk on a room it is not in.
    _seed(cn)
    book = _Book(cn)
    root = rpc._h_send(
        book,
        {"src": "sa_sender", "dst": "sa_recip", "body": "room root2", "name": "sa-room2"},
        "unit",
        "sa_sender",
    )
    rid = int(root["id"])
    with pytest.raises(CoordError) as ei:
        rpc._h_add_remove(
            book,
            {"verb": "add", "type": "mail", "id": rid, "who": "sa_third"},
            "unit",
            "sa_outsider",
        )
    assert "not allowed" in str(ei.value).lower()
    assert "sa_third" not in rec_mail.room_participants(cn, rid)
    out = rpc._h_add_remove(
        book, {"verb": "add", "type": "mail", "id": rid}, "unit", "sa_outsider"
    )
    assert out["ok"] is True
    assert "sa_outsider" in rec_mail.room_participants(cn, rid)


def test_outsider_reads_then_replies_into_room_opened_from_direct_letter(cn):
    _seed(cn)
    book = _Book(cn)
    sent = rpc._h_send(
        book, {"src": "sa_sender", "dst": "sa_recip", "body": "root3"}, "unit", "sa_sender"
    )
    mid = int(sent["id"])
    rep = rpc._h_reply(book, {"mail_id": mid, "body": "answer"}, "unit", "sa_recip")
    assert rec_tree.on_tree(cn, "mail", mid)
    got = rpc._h_mail_thread(book, {"mail_id": mid, "scope": "room"}, "unit", "sa_outsider")
    assert {int(m["id"]) for m in got["chain"]} == {mid, int(rep["id"])}
    # reading did not join
    assert "sa_outsider" not in rec_mail.room_participants(cn, mid)
    rpc._h_reply(book, {"mail_id": int(rep["id"]), "body": "me too"}, "unit", "sa_outsider")
    assert "sa_outsider" in rec_mail.room_participants(cn, mid)


def test_added_desk_can_then_reply(cn):
    _seed(cn)
    book = _Book(cn)
    sent = rpc._h_send(
        book, {"src": "sa_sender", "dst": "sa_recip", "body": "root4"}, "unit", "sa_sender"
    )
    mid = int(sent["id"])
    rpc._h_add_remove(
        book, {"verb": "add", "type": "mail", "id": mid, "who": "sa_third"}, "unit", "sa_sender"
    )
    rep = rpc._h_reply(book, {"mail_id": mid, "body": "thanks"}, "unit", "sa_third")
    assert int(rep["id"]) > mid


def test_outsider_cannot_remove_from_private_letter(cn):
    _seed(cn)
    book = _Book(cn)
    sent = rpc._h_send(
        book, {"src": "sa_sender", "dst": "sa_recip", "body": "root5"}, "unit", "sa_sender"
    )
    mid = int(sent["id"])
    with pytest.raises(CoordError):
        rpc._h_add_remove(
            book,
            {"verb": "remove", "type": "mail", "id": mid, "who": "sa_recip"},
            "unit",
            "sa_outsider",
        )
    assert "sa_recip" in _desks(cn, mid)
