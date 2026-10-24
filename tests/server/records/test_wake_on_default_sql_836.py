"""Card 836 on a real book: wake_on defaults to addressed, and the ensure step
moves seats still on the old default once. Regression row F127 (room-copy-quiet)."""
from __future__ import annotations

import pytest

from agent_coord.client.tokens import token_hash
from agent_coord.install import migrate
from agent_coord.server.records import join as rec_join
from tests.server.records.conftest import seed_names

pytestmark = pytest.mark.sql

URL = "https://hooks.example.test/automations/webhook/fx836-routine"
KEY = "fx836-key-0123456789"


def _default(cn) -> str:
    cur = cn.cursor()
    cur.execute(
        "SELECT COLUMN_DEFAULT FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'seat' AND COLUMN_NAME = 'wake_on'"
    )
    got = str(cur.fetchone()[0]).strip("'")
    cur.close()
    return got


def test_wake_on_default_and_the_one_time_move(cn):
    seed_names(cn, ("fx836", "roster"), ("fx836-d1", "desk"), ("fx836-d2", "desk"))
    for d in ("fx836-d1", "fx836-d2"):
        rec_join.upsert(cn, "fx836", d, "", token_hash("seat-" + d), None)
    cn.commit()
    assert _default(cn) == "addressed"
    rec_join.wake_arm(cn, "fx836-d1", URL, KEY)
    assert rec_join.wake_state(cn, "fx836-d1")["wake_on"] == "addressed"

    # A book from before card 836: the old column default, both seats on all.
    cur = cn.cursor()
    cur.execute("ALTER TABLE seat ALTER COLUMN wake_on SET DEFAULT 'all'")
    cur.close()
    for d in ("fx836-d1", "fx836-d2"):
        rec_join.wake_arm(cn, d, URL, KEY, wake_on="all")
    cn.commit()
    assert migrate._ensure_seat_wake_on_default(cn) == ["seat.wake_on.default.addressed"]
    assert _default(cn) == "addressed"
    assert {rec_join.wake_state(cn, d)["wake_on"] for d in ("fx836-d1", "fx836-d2")} == {"addressed"}

    # Second run changes nothing, and a desk that chooses all afterwards keeps it.
    rec_join.wake_arm(cn, "fx836-d2", URL, KEY, wake_on="all")
    cn.commit()
    assert migrate._ensure_seat_wake_on_default(cn) == []
    assert rec_join.wake_state(cn, "fx836-d2")["wake_on"] == "all"
