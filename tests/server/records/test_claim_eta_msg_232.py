"""claim stores --eta and --msg, and refuses a bad value before writing (#232)."""
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


def _open(book, cn, need: str) -> None:
    rpc._h_open(book, {"need": need}, "unit", "a")


def test_claim_wires_eta_and_msg_and_refuses_bad_values(cn) -> None:
    seed_names(cn, ("unit", "roster"), ("a", "desk"))
    book = _Book(cn)

    _open(book, cn, "c232-plain")
    plain = rpc._h_claim(book, {"need": "c232-plain"}, "unit", "a")
    assert plain["status"] == "claimed"
    assert "eta_at" not in plain
    assert "note" not in plain

    _open(book, cn, "c232-good")
    good = rpc._h_claim(
        book, {"need": "c232-good", "eta": "2h", "msg": "hi"}, "unit", "a"
    )
    assert good["status"] == "claimed"
    assert good["eta_at"]
    assert good["note"] == "hi"
    hit = rec_todo.find(cn, "unit", "c232-good")
    fields = rec_todo.unpack(hit.get("body") or "", hit.get("id"))
    assert fields["payload"]["eta_at"] == good["eta_at"]
    assert "hi" in str(fields["detail"])

    _open(book, cn, "c232-bad-eta")
    with pytest.raises(CoordError, match="claim: eta must be"):
        rpc._h_claim(book, {"need": "c232-bad-eta", "eta": "banana"}, "unit", "a")
    bad = rec_todo.find(cn, "unit", "c232-bad-eta")
    assert str(bad.get("status") or "") != "claimed"

    _open(book, cn, "c232-long")
    with pytest.raises(CoordError, match="claim: msg would be 4097 chars"):
        rpc._h_claim(book, {"need": "c232-long", "msg": "x" * 4097}, "unit", "a")
    long = rec_todo.find(cn, "unit", "c232-long")
    assert str(long.get("status") or "") != "claimed"
