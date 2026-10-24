"""Every letter row names its sender desk under one key, `from` (card 837).

`mail-thread --subtree` (and every full read) printed `sender: {deskId, roster}`
while `mail-thread --room` and `inbox` short rows printed `from: "desk"`; a desk
parsing both paid a retry. Now every letter the office returns carries
`from` (the desk name, a string) next to `sender {deskId, roster}`, and short
rows keep `from`. The push arrival carries `from` too.

Regression row F128 (mail-sender-from).
"""
from __future__ import annotations

from agent_coord.client.mail_rows import short_letter
from agent_coord.server.mail_push import compact_mail
from agent_coord.server.records.mail import public_mail


def _row():
    return {"id": 7, "created": "2026-10-23 19:00:00", "desk": "gardener",
            "sender_roster": "the-mill", "body": "hi"}


def test_full_letter_has_from_string():
    out = public_mail(_row(), [{"desk": "builder", "receipt": 0}])
    assert out["from"] == "gardener"
    assert out["sender"] == {"deskId": "gardener", "roster": "the-mill"}


def test_short_row_from_matches_full_row():
    full = public_mail(_row(), [{"desk": "builder", "receipt": 0}])
    short = short_letter(full)
    assert short["from"] == full["from"] == "gardener"
    assert "sender" not in short


def test_short_row_from_a_legacy_string_sender():
    assert short_letter({"id": 1, "sender": "wall-ui", "body": "x"})["from"] == "wall-ui"


def test_push_arrival_has_from():
    item = compact_mail({"id": 7, "desk": "gardener", "body": "hi"}, [{"desk": "builder"}], "builder")
    assert item["from"] == "gardener" and item["sender"] == "gardener"
