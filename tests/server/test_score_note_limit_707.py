"""#707: an over-limit score note is refused with the limit in plain words, no book text."""
from __future__ import annotations

import pytest

from agent_coord.helpers.errors import CoordError
from agent_coord.server import score_series as ss


class _Book:
    _cn = None


@pytest.fixture
def rec(monkeypatch):
    from agent_coord.server.api.mill import rpc
    from agent_coord.server.records import score as rec_score

    calls: list[tuple] = []

    def add(cn, project, desk, kpi, value, **kw):
        calls.append(("add", kw.get("note")))
        return [{"id": 7, "point_id": 1}]

    monkeypatch.setattr(rec_score, "point_add", add)
    monkeypatch.setattr(rec_score, "points", lambda *a, **k: [])
    monkeypatch.setattr(rpc, "_poke", lambda *a, **k: None)
    return rpc, calls


def test_note_limit_matches_the_column():
    assert ss.NOTE_MAX == 200


def test_long_note_refused_with_the_limit(rec):
    rpc, calls = rec
    with pytest.raises(CoordError) as ei:
        rpc._h_score(_Book(), {"name": "x", "value": "1", "note": "n" * 201}, "unit", "d1")
    msg = str(ei.value)
    assert msg == "score: --note is 201 characters; the most is 200, one line; nothing stored"
    assert "1406" not in msg and "p_note" not in msg
    assert calls == []


def test_note_at_the_limit_is_recorded(rec):
    rpc, calls = rec
    try:
        rpc._h_score(_Book(), {"name": "x", "value": "1", "note": "n" * 200}, "unit", "d1")
    except CoordError:
        pass  # the read-back finds no points; the write is what counts here
    assert calls == [("add", "n" * 200)]


def test_help_names_the_limit():
    from agent_coord.__main__ import _build_parser

    sub = next(a for a in _build_parser()._actions if a.dest == "cmd" or getattr(a, "choices", None))
    score = sub.choices["score"]
    note = next(a for a in score._actions if "--note" in a.option_strings)
    assert "200" in note.help
