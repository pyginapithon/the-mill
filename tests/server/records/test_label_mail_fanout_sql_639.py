"""Card #639 on a real book: `label mail ID NAME` keeps the label and posts no alert.

Before the fix the label poke ran `mill_watcher_select('mail', ...)`, the ENUM
refused it (1265 Data truncated for column 'p_type') and the wall mailed the
Admins a `fanout mail N` alert for every labelled letter.

Regression row F76 (label-mail-fanout).
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.sql

from agent_coord.server import push
from agent_coord.server.api.mill import rpc
from agent_coord.server.records import mail as rec_mail
from agent_coord.server.records import tree as rec_tree
from agent_coord.server.records.db import scalar
from tests.server.records.conftest import seed_names

R = "lm639"


class _Book:
    def __init__(self, cn):
        self._cn = cn


@pytest.fixture(scope="module")
def room(cn):
    seed_names(cn, (R, "roster"), ("lm_a", "desk"), ("lm_b", "desk"), ("practice", "label"))
    root = int(rec_mail.insert(cn, R, "lm_a", "lm_b", "room root")[0]["id"])
    idea = int(rec_mail.insert(cn, R, "lm_a", "lm_b", "IDEA: one")[0]["id"])
    rec_tree.create(cn, "lm639room", "mail", root)
    rec_tree.add(cn, "mail", root, "mail", idea, "lm639room")
    return {"root": root, "idea": idea}


def _labelled(cn, mid: int) -> int:
    return int(
        scalar(
            cn,
            "SELECT COUNT(*) FROM label l JOIN name n ON n.id = l.name_id"
            " WHERE l.type = 'mail' AND l.id = %s AND n.name = 'practice'",
            (mid,),
        )
        or 0
    )


def test_label_on_a_room_letter_posts_no_alert(cn, room):
    alerts = []
    before = int(scalar(cn, "SELECT COUNT(*) FROM mail") or 0)
    with patch.object(push, "mill_admin_alert", side_effect=lambda c, text, **k: alerts.append(text)):
        rpc._h_label(
            _Book(cn),
            {"verb": "label-add", "type": "mail", "id": room["idea"], "label": "practice", "ord": 1},
            R,
            "lm_a",
        )
    assert alerts == []
    assert _labelled(cn, room["idea"]) == 1
    assert int(scalar(cn, "SELECT COUNT(*) FROM mail") or 0) == before


def test_tree_move_of_a_letter_posts_no_alert(cn, room):
    alerts = []
    with patch.object(push, "mill_admin_alert", side_effect=lambda c, text, **k: alerts.append(text)):
        rpc._poke_tree(_Book(cn), "mail", room["idea"], owner="lm_a")
    assert alerts == []


def test_card_watchers_still_read_the_book(cn):
    from agent_coord.server.records import watcher as rec_w

    assert rec_w.select(cn, "todo", 999999) == []
