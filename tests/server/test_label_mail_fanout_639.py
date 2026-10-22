"""Card #639: a label on a letter (or a tree move of a letter) pokes no watcher.

Mail has recipients, not watchers (#270), so the watcher read for a letter is
empty and never reaches the ENUM in `mill_watcher_select`. Before the fix every
`mill label mail ID ...` made the wall post an Admin alert
`fanout mail N: 1265 (01000): Data truncated for column 'p_type'`.

Regression row F76 (label-mail-fanout).
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from agent_coord.server import push
from agent_coord.server.api.mill import rpc
from agent_coord.server.records import watcher as rec_w

ENUM_ERR = "1265 (01000): Data truncated for column 'p_type' at row 1"


def _book_call(cn, proc, args):
    """Stand-in for the book: the watcher ENUM refuses mail, as MySQL does."""
    if proc == "mill_watcher_select" and str(args[0]) not in ("todo", "join", "hold", "score"):
        raise Exception(ENUM_ERR)
    return []


@pytest.mark.parametrize("typ", ["mail", "MAIL", " mail "])
def test_watcher_select_for_mail_is_empty_and_skips_the_book(typ):
    with patch.object(rec_w, "call", side_effect=_book_call) as call:
        assert rec_w.select(MagicMock(), typ, 2184) == []
    call.assert_not_called()


def test_watcher_select_for_a_card_still_reads_the_book():
    with patch.object(rec_w, "call", side_effect=_book_call) as call:
        rec_w.select(MagicMock(), "todo", 5)
    call.assert_called_once()


def test_fanout_for_mail_sends_no_admin_alert():
    alerts = []
    with patch.object(rec_w, "call", side_effect=_book_call), patch.object(
        push, "mill_admin_alert", side_effect=lambda cn, text, **k: alerts.append(text)
    ), patch.object(push, "_cheap_detail", return_value="{}"):
        rows = push.fanout(MagicMock(), "mail", 2184, "MAIL")
    assert rows == []
    assert alerts == []


def test_label_on_a_letter_posts_no_alert():
    alerts = []
    with patch.object(rec_w, "call", side_effect=_book_call), patch.object(
        push, "mill_admin_alert", side_effect=lambda cn, text, **k: alerts.append(text)
    ), patch.object(push, "_cheap_detail", return_value="{}"), patch(
        "agent_coord.server.records.db.scalar", return_value="2026-10-22 10:01:22.685594"
    ):
        rpc._poke(MagicMock(), "mail", 2184, "label-add", owner="DESK_a", fresh=True)
    assert alerts == []
