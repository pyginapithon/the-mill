"""F12: a late joiner's room read shows pre-join room letters (#219)."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.sql

from agent_coord.helpers.errors import CoordError
from agent_coord.server.api.mill import rpc
from tests.server.records.conftest import seed_names


class _Book:
    def __init__(self, cn):
        self._cn = cn


def _ids(got: dict) -> set[int]:
    return {int(m["id"]) for m in got["chain"]}


def test_late_joiner_sees_prejoin_room_letters_not_private(cn) -> None:
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

    got = rpc._h_mail_thread(book, {"scope": "room", "mail_id": rid}, "unit", "late")
    assert _ids(got) == {rid, bid, cid, jid}
    assert sid not in _ids(got)
    assert got["room_letters"] == len(_ids(got))
    assert got["latest_id"] == max(rid, bid, cid, jid)

    original = rpc._h_mail_thread(book, {"scope": "room", "mail_id": rid}, "unit", "c")
    assert _ids(original) == {rid, bid, cid, jid}
    assert original["room_letters"] == 4
    assert sid not in _ids(original)

    whole = rpc._h_mail_thread(book, {"scope": "room", "mail_id": rid}, "unit", "a")
    assert _ids(whole) == {rid, bid, cid, jid, sid}
    assert whole["room_letters"] == len(_ids(whole))
    assert whole["latest_id"] == max(rid, bid, cid, jid, sid)

    with pytest.raises(CoordError) as ei:
        rpc._h_mail_thread(book, {"scope": "room", "mail_id": rid}, "unit", "out")
    assert "not a participant" in str(ei.value).lower()
