"""A card's notes share one budget; the refusal says what is left and where long text goes (#360).

Regression row F56 (note-detail-budget).
"""
from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from agent_coord.helpers.errors import CoordError
from agent_coord.server.api.mill import rpc
from agent_coord.server.records import todo as rec_todo
from agent_coord.server.records.todo import BODY_MAX


@pytest.fixture(autouse=True)
def _project_already_exists(monkeypatch):
    monkeypatch.setattr("agent_coord.server.records.name.get", lambda *a, **k: 1)


def _card(monkeypatch, detail: str) -> dict:
    stored = {"body": json.dumps({"slug": "budget", "doing": "", "detail": detail}), "n": 0}

    def fake_find(cn, project, need):
        return {"id": 9, "body": stored["body"], "asker": "builder", "volunteer": "builder"}

    def fake_update(cn, tid, desk, body=None, **k):
        stored["n"] += 1
        stored["body"] = body
        return [{"id": tid}]

    monkeypatch.setattr("agent_coord.server.records.todo.find", fake_find)
    monkeypatch.setattr("agent_coord.server.records.todo.update", fake_update)
    monkeypatch.setattr(rpc, "_poke", lambda *a, **k: None)
    return stored


def _note(text: str, **kw):
    return rpc._h_note(MagicMock(), dict({"need": "budget", "note": text}, **kw), "the-mill", "builder")


def test_every_note_reply_names_the_room_left(monkeypatch):
    stored = _card(monkeypatch, "first line")
    rec = _note("second line")
    assert rec["detail_left"] == BODY_MAX - len(stored["body"])
    assert rec["detail_left"] == rec_todo.budget_left(json.loads(stored["body"]))


def test_room_left_shrinks_with_each_note(monkeypatch):
    _card(monkeypatch, "")
    a = _note("x" * 100)["detail_left"]
    b = _note("y" * 100)["detail_left"]
    assert a - b == 102  # 100 characters and the newline (stored as a 2-character escape)


def test_a_note_that_changes_nothing_still_names_the_room_left(monkeypatch):
    stored = _card(monkeypatch, "kept")
    rec = rpc._h_note(MagicMock(), {"need": "budget", "eta": "", "started": False, "text": "9/12"},
                      "the-mill", "builder")
    assert rec["detail_left"] <= BODY_MAX - len(json.dumps({"slug": "budget", "doing": "", "detail": "kept"}))
    assert stored["n"] in (0, 1)


def test_over_the_budget_states_need_left_and_the_letter_route(monkeypatch):
    base = "d" * 3900
    stored = _card(monkeypatch, base)
    before = stored["body"]
    left = BODY_MAX - len(before)
    note = "n" * (left + 50)
    with pytest.raises(CoordError) as e:
        _note(note)
    msg = str(e.value)
    assert "refused, nothing written" in msg
    assert f"has {left} left of its {BODY_MAX}" in msg
    assert f"needs {len(note) + 2} characters" in msg  # the note and its newline (stored as a 2-character escape)
    assert "one budget" in msg and "room letter" in msg and "mill reply <mail_id> --body-file PATH" in msg
    assert "--replace" not in msg  # no such CLI flag
    assert stored["body"] == before and stored["n"] == 0


def test_exactly_at_the_budget_is_kept(monkeypatch):
    stored = _card(monkeypatch, "")
    left = BODY_MAX - len(stored["body"])
    rec = _note("z" * (left - 1))  # the first note adds no newline; one char margin for safety
    assert rec["detail_left"] == 1


def test_escaped_characters_count_as_stored(monkeypatch):
    stored = _card(monkeypatch, "")
    left = BODY_MAX - len(stored["body"])
    with pytest.raises(CoordError, match="refused, nothing written"):
        _note("\u00e9" * (left // 6 + 1))  # each stores as \\u00e9 (6 characters)
    assert stored["n"] == 0


def test_over_budget_helper_is_empty_when_it_fits():
    small = {"slug": "s", "doing": "", "detail": "a"}
    assert rec_todo.over_budget(small, dict(small, detail="ab")) == ""
