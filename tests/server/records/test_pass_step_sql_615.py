"""pass names its step, on a real book (#615). Regression row F67 (pass-step).

Seen live: pass run again on cards already shipped moved them to done with
no word, and the client had no way to set them back. pass on a done or
parked card also moved it to shipped.
"""
from __future__ import annotations

import pytest

from agent_coord.helpers.errors import CoordError
from agent_coord.server.api.mill import rpc
from agent_coord.server.records import todo as rec_todo
from tests.server.records.conftest import seed_names

pytestmark = pytest.mark.sql


class _Book:
    def __init__(self, cn):
        self._cn = cn


def _status(cn, need):
    return rec_todo.find(cn, "unit", need)["status"]


def _card(cn, need, asker="a615", vol="v615"):
    seed_names(cn, ("unit", "roster"), (asker, "desk"), (vol, "desk"))
    book = _Book(cn)
    rpc._h_open(book, {"need": need}, "unit", asker)
    rpc._h_claim(book, {"need": need}, "unit", vol)
    return book


def test_pass_ships_then_a_repeat_is_refused_and_changes_nothing(cn):
    book = _card(cn, "p615-a")
    assert rpc._h_pass(book, {"need": "p615-a"}, "unit", "v615")["status"] == "shipped"
    with pytest.raises(CoordError) as e:
        rpc._h_pass(book, {"need": "p615-a"}, "unit", "v615")
    assert str(e.value) == "pass: p615-a is already shipped; the asker accepts it with mill pass unit p615-a --done"
    assert _status(cn, "p615-a") == "shipped"


def test_a_desk_that_is_asker_and_volunteer_needs_done_to_finish(cn):
    book = _card(cn, "p615-b", asker="s615", vol="s615")
    rpc._h_pass(book, {"need": "p615-b"}, "unit", "s615")
    with pytest.raises(CoordError, match="already shipped"):
        rpc._h_pass(book, {"need": "p615-b"}, "unit", "s615")
    assert rpc._h_pass(book, {"need": "p615-b", "step": "done"}, "unit", "s615")["status"] == "done"


def test_done_needs_a_shipped_card(cn):
    book = _card(cn, "p615-c")
    with pytest.raises(CoordError) as e:
        rpc._h_pass(book, {"need": "p615-c", "step": "done"}, "unit", "a615")
    assert str(e.value) == "pass --done: p615-c is claimed, not shipped; nothing changed"
    assert _status(cn, "p615-c") == "claimed"


def test_pass_on_a_done_card_is_refused_not_reopened(cn):
    book = _card(cn, "p615-d")
    rpc._h_pass(book, {"need": "p615-d"}, "unit", "v615")
    rpc._h_pass(book, {"need": "p615-d", "step": "done"}, "unit", "a615")
    with pytest.raises(CoordError) as e:
        rpc._h_pass(book, {"need": "p615-d"}, "unit", "v615")
    assert str(e.value) == "pass: p615-d is already done; mill pass unit p615-d --back steps it back to shipped"
    assert _status(cn, "p615-d") == "done"


def test_back_steps_done_to_shipped_to_claimed(cn):
    book = _card(cn, "p615-e")
    rpc._h_pass(book, {"need": "p615-e"}, "unit", "v615")
    rpc._h_pass(book, {"need": "p615-e", "step": "done"}, "unit", "a615")
    assert rpc._h_pass(book, {"need": "p615-e", "step": "back"}, "unit", "a615")["status"] == "shipped"
    assert rpc._h_pass(book, {"need": "p615-e", "step": "back"}, "unit", "v615")["status"] == "claimed"
    hit = rec_todo.find(cn, "unit", "p615-e")
    assert rpc._desk_slug(cn, hit, "volunteer", "assigned") == "v615"
    with pytest.raises(CoordError) as e:
        rpc._h_pass(book, {"need": "p615-e", "step": "back"}, "unit", "v615")
    assert str(e.value) == "pass --back: p615-e is claimed; only shipped or done steps back (unclaim releases a claim)"


def test_back_and_done_are_the_asker_or_volunteer(cn):
    seed_names(cn, ("o615", "desk"))
    book = _card(cn, "p615-f")
    rpc._h_pass(book, {"need": "p615-f"}, "unit", "v615")
    with pytest.raises(CoordError, match="who-may"):
        rpc._h_pass(book, {"need": "p615-f", "step": "back"}, "unit", "o615")
    with pytest.raises(CoordError, match="who-may"):
        rpc._h_pass(book, {"need": "p615-f", "step": "done"}, "unit", "o615")
    assert _status(cn, "p615-f") == "shipped"


def test_an_unknown_step_is_refused(cn):
    book = _card(cn, "p615-g")
    with pytest.raises(CoordError, match="pass: step is ship, done or back"):
        rpc._h_pass(book, {"need": "p615-g", "step": "close"}, "unit", "v615")
