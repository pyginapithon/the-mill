"""done_when and pass evidence on a real book (card 866). Row F143."""
from __future__ import annotations

import json

import pytest

from agent_coord.helpers.errors import CoordError
from agent_coord.server.api.mill import rpc
from agent_coord.server.records import todo as rec_todo
from tests.server.records.conftest import seed_names

pytestmark = pytest.mark.sql


class _Book:
    def __init__(self, cn):
        self._cn = cn


def _open(cn, need, asker="a866", vol="v866"):
    seed_names(cn, ("unit", "roster"), (asker, "desk"), (vol, "desk"))
    book = _Book(cn)
    rpc._h_open(book, {"need": need}, "unit", asker)
    rpc._h_claim(book, {"need": need}, "unit", vol)
    return book


def _body(cn, need):
    raw = rec_todo.find(cn, "unit", need).get("body") or ""
    return json.loads(raw)


def test_accept_sets_done_when_and_a_volunteer_is_refused(cn):
    book = _open(cn, "b866-a")
    with pytest.raises(CoordError, match="who-may"):
        rpc._h_accept(book, {"need": "b866-a", "done_when": "tests green"}, "unit", "v866")
    assert "done_when" not in _body(cn, "b866-a")
    got = rpc._h_accept(book, {"need": "b866-a", "done_when": "tests green"}, "unit", "a866")
    assert got["done_when"] == "tests green"
    assert _body(cn, "b866-a")["done_when"] == "tests green"
    assert rec_todo.find(cn, "unit", "b866-a")["status"] == "claimed"
    card = rpc._h_todo(book, {"need": "b866-a"}, "unit", "a866")
    assert card[0]["done_when"] == "tests green"
    cleared = rpc._h_accept(book, {"need": "b866-a", "done_when": "  "}, "unit", "a866")
    assert cleared["done_when"] is None
    assert "done_when" not in _body(cn, "b866-a")


def test_pass_stores_evidence_and_back_clears_it(cn):
    book = _open(cn, "b866-b")
    rpc._h_pass(book, {"need": "b866-b", "step": "ship", "evidence": "the log"}, "unit", "v866")
    assert _body(cn, "b866-b")["evidence"] == "the log"
    assert rec_todo.find(cn, "unit", "b866-b")["status"] == "shipped"
    rpc._h_pass(book, {"need": "b866-b", "step": "back", "evidence": "nope"}, "unit", "a866")
    assert "evidence" not in _body(cn, "b866-b")
    assert rec_todo.find(cn, "unit", "b866-b")["status"] == "claimed"
