"""note --supersedes on a real book (#333)."""
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


def _detail(cn) -> str:
    hit = rec_todo.find(cn, "unit", "c333-card")
    return str(rec_todo.unpack(hit.get("body") or "", hit.get("id"))["detail"])


def test_asker_supersedes_and_other_desk_is_refused(cn) -> None:
    seed_names(cn, ("unit", "roster"), ("c333-asker", "desk"), ("c333-other", "desk"))
    book = _Book(cn)
    rpc._h_open(book, {"need": "c333-card", "detail": "1. connect old-pilot\n2. read"}, "unit", "c333-asker")

    with pytest.raises(CoordError, match="asker"):
        rpc._h_note(book, {"need": "c333-card", "supersedes": "1. connect old-pilot", "note": "x"}, "unit", "c333-other")
    assert _detail(cn) == "1. connect old-pilot\n2. read"

    r = rpc._h_note(
        book,
        {"need": "c333-card", "supersedes": "1. connect old-pilot", "note": "1. connect github-pilot"},
        "unit",
        "c333-asker",
    )
    assert r["changed"] is True
    assert _detail(cn) == "[superseded] 1. connect old-pilot\n1. connect github-pilot\n2. read"
