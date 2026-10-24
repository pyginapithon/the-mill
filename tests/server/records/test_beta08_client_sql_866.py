"""Pass evidence is not written onto the card body (card 866). Row F143.

The server stores evidence. On today's book the client sends it and this
handler leaves the body alone.
"""
from __future__ import annotations

import json

import pytest

from agent_coord.server.api.mill import rpc
from agent_coord.server.records import todo as rec_todo
from tests.server.records.conftest import seed_names

pytestmark = pytest.mark.sql


class _Book:
    def __init__(self, cn):
        self._cn = cn


def test_pass_does_not_store_evidence_on_the_card_body(cn):
    seed_names(cn, ("unit", "roster"), ("a866", "desk"), ("v866", "desk"))
    book = _Book(cn)
    rpc._h_open(book, {"need": "b866-b"}, "unit", "a866")
    rpc._h_claim(book, {"need": "b866-b"}, "unit", "v866")
    rpc._h_pass(book, {"need": "b866-b", "step": "ship", "evidence": "the log"}, "unit", "v866")
    raw = rec_todo.find(cn, "unit", "b866-b").get("body") or ""
    body = json.loads(raw) if raw else {}
    assert "evidence" not in body
    assert rec_todo.find(cn, "unit", "b866-b")["status"] == "shipped"
