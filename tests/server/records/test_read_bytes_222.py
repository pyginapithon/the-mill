"""#222: a later branch read does not reprint a letter this desk sent.

Per-reply stdout stays within 1.5x of the first read. Round 4's passing arm
was 1.17x. The asked letter is kept. Another desk's unread letter is kept.
--full still returns the whole branch. The first read (cursor still unset)
still includes a letter this desk sent.
"""
from __future__ import annotations

import json

import pytest

pytestmark = pytest.mark.sql

from agent_coord.server.api.mill import rpc
from tests.server.records.conftest import seed_names
from tests.server.records.test_room_reply import _Book

BODY = "A9 note. Answer this letter by id. Same length on every reply."


def _ids(out: dict) -> list[int]:
    return [int(m["id"]) for m in out.get("chain") or []]


def _stdout_bytes(result: dict) -> int:
    env = {
        "id": "00000000-0000-0000-0000-000000000000",
        "ok": True,
        "result": result,
        "sync": [],
        "mill": "0.6.33",
    }
    raw = json.dumps(env, default=str, indent=2)
    return len(raw.encode("utf-8"))


def test_per_reply_reads_stay_within_1_5x(cn) -> None:
    """Both desks answer the root, then each answers the peer. Four reads."""
    a, b = "rba", "rbb"
    seed_names(cn, ("unit", "roster"), (a, "desk"), (b, "desk"))
    book = _Book(cn)
    root = int(
        rpc._h_send(
            book,
            {"src": a, "dst": b, "body": "root welcome", "name": "rb-room"},
            "unit",
            a,
        )["id"]
    )
    rpc._h_mail_thread(book, {"mail_id": root}, "unit", a)
    rpc._h_mail_thread(book, {"mail_id": root}, "unit", b)
    rpc._h_reply(book, {"mail_id": root, "body": BODY + " A4"}, "unit", a)
    asked = int(rpc._h_reply(book, {"mail_id": root, "body": BODY + " B4"}, "unit", b)["id"])
    sizes: list[int] = []
    for n in range(1, 5):
        got = rpc._h_mail_thread(book, {"mail_id": asked}, "unit", a)
        assert _ids(got) == [asked], _ids(got)
        sizes.append(_stdout_bytes(got))
        mine = int(rpc._h_reply(book, {"mail_id": asked, "body": BODY + f" A{n}"}, "unit", a)["id"])
        if n == 4:
            break
        asked = int(
            rpc._h_reply(book, {"mail_id": mine, "body": BODY + f" B{n + 1}"}, "unit", b)["id"]
        )
    assert sizes[0] > 0
    assert max(sizes) / sizes[0] <= 1.5


def test_later_read_keeps_another_desks_letter(cn) -> None:
    a, b, c = "oba", "obb", "obc"
    seed_names(cn, ("unit", "roster"), (a, "desk"), (b, "desk"), (c, "desk"))
    book = _Book(cn)
    root = int(
        rpc._h_send(
            book, {"src": a, "dst": f"{b},{c}", "body": "root", "name": "ob-room"}, "unit", a
        )["id"]
    )
    rpc._h_mail_thread(book, {"mail_id": root}, "unit", a)
    b1 = int(rpc._h_reply(book, {"mail_id": root, "body": "from b"}, "unit", b)["id"])
    a2 = int(rpc._h_reply(book, {"mail_id": b1, "body": "from a"}, "unit", a)["id"])
    c1 = int(rpc._h_reply(book, {"mail_id": a2, "body": "from c"}, "unit", c)["id"])
    got = rpc._h_mail_thread(book, {"mail_id": c1}, "unit", a)
    assert _ids(got) == [b1, c1]


def test_reread_of_own_letter_returns_it(cn) -> None:
    a, b = "owa", "owb"
    seed_names(cn, ("unit", "roster"), (a, "desk"), (b, "desk"))
    book = _Book(cn)
    root = int(
        rpc._h_send(
            book, {"src": a, "dst": b, "body": "root", "name": "ow-room"}, "unit", a
        )["id"]
    )
    rpc._h_mail_thread(book, {"mail_id": root}, "unit", a)
    mine = int(rpc._h_reply(book, {"mail_id": root, "body": "mine"}, "unit", a)["id"])
    peer = int(rpc._h_reply(book, {"mail_id": mine, "body": "peer"}, "unit", b)["id"])
    rpc._h_mail_thread(book, {"mail_id": peer}, "unit", a)
    again = rpc._h_mail_thread(book, {"mail_id": mine}, "unit", a)
    assert _ids(again) == [mine]


def test_full_still_includes_own_letters(cn) -> None:
    a, b = "fua", "fub"
    seed_names(cn, ("unit", "roster"), (a, "desk"), (b, "desk"))
    book = _Book(cn)
    root = int(
        rpc._h_send(
            book, {"src": a, "dst": b, "body": "root", "name": "fu-room"}, "unit", a
        )["id"]
    )
    rpc._h_mail_thread(book, {"mail_id": root}, "unit", a)
    mine = int(rpc._h_reply(book, {"mail_id": root, "body": "mine"}, "unit", a)["id"])
    peer = int(rpc._h_reply(book, {"mail_id": mine, "body": "peer"}, "unit", b)["id"])
    rpc._h_mail_thread(book, {"mail_id": peer}, "unit", a)
    full = rpc._h_mail_thread(book, {"mail_id": peer, "scope": "full"}, "unit", a)
    assert _ids(full) == [root, mine, peer]


def test_first_read_still_includes_own_root(cn) -> None:
    a, b = "fia", "fib"
    seed_names(cn, ("unit", "roster"), (a, "desk"), (b, "desk"))
    book = _Book(cn)
    root = int(
        rpc._h_send(
            book, {"src": a, "dst": b, "body": "root", "name": "fi-room"}, "unit", a
        )["id"]
    )
    peer = int(rpc._h_reply(book, {"mail_id": root, "body": "peer"}, "unit", b)["id"])
    got = rpc._h_mail_thread(book, {"mail_id": peer}, "unit", a)
    assert _ids(got) == [root, peer]
