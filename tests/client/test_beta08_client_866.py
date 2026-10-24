"""Card 866: show done_when, pass --evidence, cached glance. Row F143."""
from __future__ import annotations

import pytest

from agent_coord.__main__ import _build_parser
from agent_coord.client.outbound import body_from_args
from agent_coord.helpers.errors import CoordError
from agent_coord.server.api.mill.rpc import _todo_card
from agent_coord.server.beta_client import (
    check_accept,
    done_when_text,
    evidence_for_pass,
    read_cached_glance,
    shape_glance,
)


def _card(row, fields):
    return _todo_card(row, "unit", "open", fields)


def test_pass_sends_evidence():
    args = _build_parser().parse_args(["pass", "unit", "n1", "--evidence", "the log"])
    body = body_from_args(args)
    assert body["step"] == "ship"
    assert body["evidence"] == "the log"


def test_blank_evidence_is_omitted():
    args = _build_parser().parse_args(["pass", "unit", "n1", "--evidence", "  "])
    body = body_from_args(args)
    assert "evidence" not in body


def test_evidence_over_2000_is_refused():
    args = _build_parser().parse_args(["pass", "unit", "n1", "--evidence", "x" * 2001])
    with pytest.raises(CoordError, match="0..2000"):
        body_from_args(args)


def test_back_sends_evidence_for_the_server_to_drop():
    args = _build_parser().parse_args(["pass", "unit", "n1", "--back", "--evidence", "nope"])
    body = body_from_args(args)
    assert body["step"] == "back"
    assert body["evidence"] == "nope"


def test_card_shows_done_when_from_the_row():
    card = _card(
        {"id": 1, "done_when": "tests green"},
        {"need_id": "n", "detail": "d", "progress": "", "payload": None},
    )
    assert card["done_when"] == "tests green"


def test_card_omits_done_when_when_unset():
    card = _card(
        {"id": 1},
        {"need_id": "n", "detail": "d", "progress": "", "payload": None},
    )
    assert "done_when" not in card


def test_card_reads_done_when_from_the_body():
    card = _card(
        {"id": 1},
        {"need_id": "n", "detail": "d", "progress": "", "payload": {"done_when": "from body"}},
    )
    assert card["done_when"] == "from body"


def test_glance_sends_the_command():
    args = _build_parser().parse_args(["glance"])
    body = body_from_args(args)
    assert body["verb"] == "glance"


def test_accept_sends_done_when():
    args = _build_parser().parse_args(["accept", "unit", "n1", "--done-when", "tests green"])
    body = body_from_args(args)
    assert body["verb"] == "accept"
    assert body["done_when"] == "tests green"


def test_glance_keeps_two_sets_and_drops_unread():
    got = shape_glance(
        [{
            "id": 1, "at": "t", "refresh_us": 1, "present": 2, "held": 0,
            "open_n": 1, "claimed_n": 0, "parked_n": 0, "shipped_n": 0, "done_n": 0,
            "letters_1d": 3, "card_moves_1d": 0, "doings_1d": 0, "holds_1d": 0, "points_1d": 0,
            "open_votes": 4, "unread": 99,
        }],
        [{"seq": 1, "at": "t", "kind": "letter", "ref": 5, "desk": "a"}],
    )
    assert got["cache"]["present"] == 2
    assert got["cache"]["open_votes"] == 4
    assert "unread" not in got["cache"]
    assert got["activity"] == [{"seq": 1, "at": "t", "kind": "letter", "ref": 5, "desk": "a"}]


def test_glance_caps_activity_at_30():
    rows = [{"seq": i, "at": "t", "kind": "card", "ref": i, "desk": "a"} for i in range(40)]
    assert len(shape_glance([], rows)["activity"]) == 30


def test_evidence_back_stores_nothing():
    assert evidence_for_pass("back", "text") is None
    assert evidence_for_pass("ship", "  the log  ") == "the log"
    assert evidence_for_pass("done", "   ") is None


def test_accept_rules():
    assert done_when_text("  ship it  ") == "ship it"
    assert done_when_text("   ") is None
    with pytest.raises(CoordError, match="0..1000"):
        done_when_text("y" * 1001)
    with pytest.raises(CoordError, match="done or gone"):
        check_accept("done", "asker", "asker", False)
    with pytest.raises(CoordError, match="who-may"):
        check_accept("open", "volunteer", "asker", False)
    check_accept("claimed", "asker", "asker", False)
    check_accept("open", "other", "asker", True)


def test_column_wins_over_the_body():
    card = _card(
        {"id": 1, "done_when": "from row"},
        {"need_id": "n", "detail": "d", "progress": "", "payload": {"done_when": "from body"}},
    )
    assert card["done_when"] == "from row"


def test_accept_requires_done_when():
    args = _build_parser().parse_args(["accept", "unit", "n1"])
    with pytest.raises(CoordError, match="--done-when is required"):
        body_from_args(args)


def test_glance_refuses_when_the_read_is_missing():
    class _Cur:
        def execute(self, _sql):
            raise RuntimeError('(1305, "PROCEDURE uc_a6_glance_cached does not exist")')

        def close(self):
            return None

    class _Cn:
        def cursor(self, dictionary=True):
            return _Cur()

    with pytest.raises(CoordError, match="not installed"):
        read_cached_glance(_Cn())


def test_glance_other_read_errors_are_refused():
    class _Cur:
        def execute(self, _sql):
            raise RuntimeError("lost connection")

        def close(self):
            return None

    class _Cn:
        def cursor(self, dictionary=True):
            return _Cur()

    with pytest.raises(CoordError, match="could not be read"):
        read_cached_glance(_Cn())


def test_glance_reads_the_two_sets():
    class _Cur:
        def __init__(self):
            self.i = 0
            self.with_rows = True

        def execute(self, sql):
            assert sql == "CALL uc_a6_glance_cached()"

        def fetchall(self):
            if self.i == 0:
                return [{
                    "id": 1, "at": "t", "refresh_us": 3, "present": 1, "held": 0,
                    "open_n": 0, "claimed_n": 0, "parked_n": 0, "shipped_n": 0, "done_n": 0,
                    "letters_1d": 0, "card_moves_1d": 0, "doings_1d": 0, "holds_1d": 0,
                    "points_1d": 0, "unread": 7,
                }]
            return [{"seq": 9, "at": "t", "kind": "score", "ref": 4, "desk": "a", "extra": 1}]

        def nextset(self):
            self.i += 1
            return self.i == 1

        def close(self):
            return None

    class _Cn:
        def cursor(self, dictionary=True):
            return _Cur()

    got = read_cached_glance(_Cn())
    assert got["cache"]["refresh_us"] == 3
    assert "unread" not in got["cache"]
    assert got["activity"] == [{"seq": 9, "at": "t", "kind": "score", "ref": 4, "desk": "a"}]
