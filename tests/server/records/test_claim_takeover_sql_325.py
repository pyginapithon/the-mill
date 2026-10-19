"""claim on a card another desk holds, on a real book (#325)."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.sql

from agent_coord.helpers.errors import CoordError
from agent_coord.server.api.mill import rpc
from agent_coord.server.records import todo as rec_todo
from tests.server.records.conftest import seed_names


class _Book:
    def __init__(self, cn):
        self._cn = cn


def test_claim_held_card_refused_then_take_over_records_prior(cn) -> None:
    seed_names(cn, ("unit", "roster"), ("w1", "desk"), ("w3", "desk"))
    book = _Book(cn)
    rpc._h_open(book, {"need": "c325-held"}, "unit", "w3")
    rpc._h_claim(book, {"need": "c325-held"}, "unit", "w3")

    with pytest.raises(CoordError, match="claimed by w3"):
        rpc._h_claim(book, {"need": "c325-held", "msg": "mine"}, "unit", "w1")
    hit = rec_todo.find(cn, "unit", "c325-held")
    assert rpc._desk_slug(cn, hit, "volunteer", "assigned") == "w3"
    assert "mine" not in str(rec_todo.unpack(hit.get("body") or "", hit.get("id"))["detail"])

    again = rpc._h_claim(book, {"need": "c325-held"}, "unit", "w3")
    assert "prior_volunteer" not in again

    took = rpc._h_claim(book, {"need": "c325-held", "take_over": True}, "unit", "w1")
    assert took["prior_volunteer"] == "w3"
    hit = rec_todo.find(cn, "unit", "c325-held")
    assert rpc._desk_slug(cn, hit, "volunteer", "assigned") == "w1"
    assert "took over from w3" in str(rec_todo.unpack(hit.get("body") or "", hit.get("id"))["detail"])
