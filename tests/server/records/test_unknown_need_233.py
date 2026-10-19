"""pass, unclaim, and unpark refuse an unknown need before writing (#233)."""
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


def test_unknown_and_removed_need_refuses(cn) -> None:
    seed_names(cn, ("unit", "roster"), ("a", "desk"))
    book = _Book(cn)
    made = rpc._h_open(book, {"need": "c233-live"}, "unit", "a")
    rec_todo.delete(cn, int(made["id"]), "a")
    assert rec_todo.find(cn, "unit", "c233-live") is None

    for verb in (rpc._h_pass, rpc._h_yield, rpc._h_unpark):
        for need in ("c233-missing", "c233-live"):
            with pytest.raises(CoordError, match="no such need: unit/" + need):
                verb(book, {"need": need}, "unit", "a")
