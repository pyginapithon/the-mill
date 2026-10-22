"""F12 then #672 (S-3): every desk reads the whole room, pre-join letters included."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.sql

from agent_coord.server.api.mill import rpc
from tests.server.records.conftest import seed_names


class _Book:
    def __init__(self, cn):
        self._cn = cn


def _ids(got: dict) -> set[int]:
    return {int(m["id"]) for m in got["chain"]}


def test_every_desk_reads_whole_room_672(cn) -> None:
    seed_names(
        cn,
        ("unit", "roster"),
        ("a", "desk"),
        ("b", "desk"),
        ("c", "desk"),
        ("late", "desk"),
        ("out", "desk"),
    )
    book = _Book(cn)
    root = rpc._h_send(
        book,
        {"src": "a", "dst": "b,c", "body": "root", "name": "f12-prejoin"},
        "unit",
        "a",
    )
    rid = int(root["id"])
    pre_b = rpc._h_reply(book, {"mail_id": rid, "body": "pre-b", "src": "b"}, "unit", "b")
    pre_c = rpc._h_reply(book, {"mail_id": rid, "body": "pre-c", "src": "c"}, "unit", "c")
    joined = rpc._h_reply(book, {"mail_id": rid, "body": "late-joins", "src": "late"}, "unit", "late")
    secret = rpc._h_reply(
        book,
        {"mail_id": rid, "body": "secret", "src": "b", "mail_tos": ["a"]},
        "unit",
        "b",
    )
    bid, cid, jid, sid = int(pre_b["id"]), int(pre_c["id"]), int(joined["id"]), int(secret["id"])

    every = {rid, bid, cid, jid, sid}
    # #672: the side letter that left c and late off is readable too; an
    # outsider reads the same room and is not made a participant.
    for desk in ("late", "c", "a", "out"):
        got = rpc._h_mail_thread(book, {"scope": "room", "mail_id": rid}, "unit", desk)
        assert _ids(got) == every, desk
        assert got["room_letters"] == len(every)
        assert got["latest_id"] == max(every)
    from agent_coord.server.records import mail as rec_mail

    assert "out" not in rec_mail.room_participants(cn, rid)
