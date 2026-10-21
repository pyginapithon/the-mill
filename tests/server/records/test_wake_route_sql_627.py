"""#627 on a real book: a burst is addressed when any waiting item is.
A stored row marked wake_reason room is a room-member copy; take() drops the
mark, so the sync item is unchanged. Row F73 (wake-route)."""
from __future__ import annotations

import pytest

from agent_coord.server.records import push as rec_push
from tests.server.records.conftest import seed_names

pytestmark = pytest.mark.sql


def test_pending_addressed_reads_the_queue(cn):
    seed_names(cn, ("fx627", "roster"), ("fx627-d1", "desk"))
    cn.commit()
    rec_push.take(cn, "fx627-d1")
    assert rec_push.pending_addressed(cn, "fx627-d1") is False
    rec_push.put(cn, "fx627-d1", "mail", {"kind": "mail", "id": 1, "wake_reason": "room"}, "missed")
    cn.commit()
    assert rec_push.pending_addressed(cn, "fx627-d1") is False
    rec_push.put(cn, "fx627-d1", "mail", {"kind": "mail", "id": 2}, "sent")  # handed live: not waiting
    cn.commit()
    assert rec_push.pending_addressed(cn, "fx627-d1") is False
    rec_push.put(cn, "fx627-d1", "hint", {"type": "todo", "id": 3}, "missed")
    cn.commit()
    assert rec_push.pending_addressed(cn, "fx627-d1") is True
    items = rec_push.take(cn, "fx627-d1")
    assert items and all("wake_reason" not in i for i in items)
    assert rec_push.pending_addressed(cn, "fx627-d1") is False


def test_an_old_letter_row_without_the_mark_is_addressed(cn):
    seed_names(cn, ("fx627", "roster"), ("fx627-d2", "desk"))
    cn.commit()
    rec_push.take(cn, "fx627-d2")
    rec_push.put(cn, "fx627-d2", "mail", {"kind": "mail", "id": 4}, "missed")
    cn.commit()
    assert rec_push.pending_addressed(cn, "fx627-d2") is True
    rec_push.take(cn, "fx627-d2")
