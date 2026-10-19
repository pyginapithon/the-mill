"""create todo refuses a status other than parked or open (#231)."""
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


def test_create_status_parked_or_open_only(cn) -> None:
    seed_names(cn, ("unit", "roster"), ("a", "desk"))
    book = _Book(cn)

    opened = rpc._h_open(book, {"need": "st231-empty"}, "unit", "a")
    assert opened["status"] == "open"
    missing = rpc._h_open(book, {"need": "st231-missing", "status": "   "}, "unit", "a")
    assert missing["status"] == "open"
    cased = rpc._h_open(book, {"need": "st231-case", "status": "OPEN"}, "unit", "a")
    assert cased["status"] == "open"
    parked = rpc._h_open(book, {"need": "st231-parked", "status": "Parked"}, "unit", "a")
    assert parked["status"] == "parked"
    plain = rpc._h_open(book, {"need": "st231-open", "status": "open"}, "unit", "a")
    assert plain["status"] == "open"

    for word in ("blocked", "claimed", "shipped", "done", "Bogus"):
        with pytest.raises(CoordError, match="status must be parked or open"):
            rpc._h_open(book, {"need": "st231-" + word.lower(), "status": word}, "unit", "a")
        assert rec_todo.find(cn, "unit", "st231-" + word.lower()) is None
