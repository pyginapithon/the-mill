"""#108 bearer lookup reads join.token_hash. It does not scan mill_join_select."""
from __future__ import annotations

import inspect

import pytest

from agent_coord.client.session_errors import SESSION_INVALID_REJOIN
from agent_coord.client.tokens import token_hash
from agent_coord.helpers.errors import CoordError
from agent_coord.server.book import Book
from agent_coord.server.records import join as rec_join


class _Cur:
    def __init__(self, row):
        self.row = row
        self.sql = ""
        self.args = ()

    def execute(self, sql, args=()):
        self.sql = sql
        self.args = args

    def fetchone(self):
        return self.row

    def close(self):
        return None


class _Cn:
    def __init__(self, row):
        self.cur = _Cur(row)

    def cursor(self, **_k):
        return self.cur


def test_desk_for_token_hash_is_a_point_lookup():
    digest = token_hash("seat-a")
    cn = _Cn(("alice",))
    assert rec_join.desk_for_token_hash(cn, digest) == "alice"
    assert "mill_join_select" not in cn.cur.sql
    assert "token_hash" in cn.cur.sql
    assert cn.cur.args == (digest,)


def test_desk_for_token_hash_empty_digest_does_not_query():
    cn = _Cn(("alice",))
    assert rec_join.desk_for_token_hash(cn, "") == ""
    assert cn.cur.sql == ""


def test_token_hash_for_desk_missing_row_is_none():
    cn = _Cn(None)
    assert rec_join.token_hash_for_desk(cn, "alice") is None


def test_token_hash_for_desk_null_hash_is_empty_string():
    cn = _Cn((None,))
    assert rec_join.token_hash_for_desk(cn, "alice") == ""


def test_token_matches_requires_equal_digest():
    digest = token_hash("seat-a")
    assert rec_join.token_matches(_Cn((digest,)), "alice", digest) is True
    assert rec_join.token_matches(_Cn((digest,)), "alice", token_hash("other")) is False
    assert rec_join.token_matches(_Cn((digest,)), "alice", "") is False
    assert rec_join.token_matches(_Cn(None), "alice", digest) is False


def test_resolve_bearer_uses_the_point_lookup(monkeypatch):
    seen = {}

    def fake(cn, digest):
        seen["digest"] = digest
        return "alice"

    monkeypatch.setattr(rec_join, "desk_for_token_hash", fake)
    book = Book.__new__(Book)
    book._cn = object()
    assert book.resolve_bearer("seat-a") == "alice"
    assert seen["digest"] == token_hash("seat-a")
    src = inspect.getsource(Book.resolve_bearer)
    assert "mill_join_select" not in src
    assert "desk_for_token_hash" in src


def test_guard_owner_matches_without_scanning_seats(monkeypatch):
    digest = token_hash("seat-a")
    monkeypatch.setattr(rec_join, "token_hash_for_desk", lambda cn, desk: digest)
    book = Book.__new__(Book)
    book._cn = object()
    book._tokens = {}
    out = book._guard_owner("the-mill", "alice", "seat-a", must_be_present=True)
    assert out == {"desk": "alice"}
    src = inspect.getsource(Book._guard_owner)
    assert "mill_join_select" not in src


def test_guard_owner_missing_seat(monkeypatch):
    monkeypatch.setattr(rec_join, "token_hash_for_desk", lambda cn, desk: None)
    book = Book.__new__(Book)
    book._cn = object()
    book._tokens = {}
    assert book._guard_owner("the-mill", "alice", "seat-a") is None
    with pytest.raises(CoordError) as ei:
        book._guard_owner("the-mill", "alice", "seat-a", must_be_present=True)
    assert str(ei.value) == SESSION_INVALID_REJOIN


def test_guard_owner_cleared_hash_fails_closed(monkeypatch):
    monkeypatch.setattr(rec_join, "token_hash_for_desk", lambda cn, desk: "")
    book = Book.__new__(Book)
    book._cn = object()
    book._tokens = {}
    with pytest.raises(CoordError) as ei:
        book._guard_owner("the-mill", "alice", "seat-a", must_be_present=True)
    assert str(ei.value) == SESSION_INVALID_REJOIN
