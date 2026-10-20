"""note --supersedes marks a detail line superseded and puts the new text under it (#333). Regression row F45 (card-edit)."""
from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from agent_coord.helpers.errors import CoordError
from agent_coord.server.api.mill import rpc

DETAIL = "Steps:\n1. connect desk old-pilot\n2. read the inbox"


@pytest.fixture
def card(monkeypatch):
    state = {"body": json.dumps({"slug": "c333", "doing": "", "detail": DETAIL}), "writes": 0}

    monkeypatch.setattr(
        "agent_coord.server.records.todo.find",
        lambda cn, p, n: {"id": 333, "body": state["body"], "creator": "asker-desk", "assigned": "w1"},
    )

    def upd(cn, tid, desk, body=None, **kw):
        if body is not None:
            state["body"] = body
            state["writes"] += 1
        return [{"id": tid}]

    monkeypatch.setattr("agent_coord.server.records.todo.update", upd)
    monkeypatch.setattr(rpc, "_poke", lambda *a, **k: None)
    monkeypatch.setattr(
        "agent_coord.server.admin.guard.is_role_admin", lambda cn, desk: desk == "admin-desk"
    )
    return state


def _detail(state):
    return json.loads(state["body"])["detail"]


def _note(body, who="asker-desk"):
    return rpc._h_note(MagicMock(), dict(need="c333", **body), "cold-test", who)


def test_asker_supersedes_a_line_and_history_stays(card):
    r = _note({"supersedes": "1. connect desk old-pilot", "note": "1. connect desk github-pilot"})
    assert _detail(card) == (
        "Steps:\n[superseded] 1. connect desk old-pilot\n1. connect desk github-pilot\n2. read the inbox"
    )
    assert r["detail"] == _detail(card)
    assert r["superseded"] == "1. connect desk old-pilot"


def test_match_ignores_spaces_at_the_ends(card):
    _note({"supersedes": "  2. read the inbox ", "note": "2. read the room"})
    assert "[superseded] 2. read the inbox\n2. read the room" in _detail(card)


def test_admin_may_supersede(card):
    _note({"supersedes": "Steps:", "note": "Steps (fixed):"}, who="admin-desk")
    assert _detail(card).startswith("[superseded] Steps:\nSteps (fixed):")


def test_non_asker_is_refused_and_nothing_written(card):
    with pytest.raises(CoordError, match="--supersedes is for the asker"):
        _note({"supersedes": "Steps:", "note": "x"}, who="w1")
    assert card["writes"] == 0


def test_no_match_is_refused(card):
    with pytest.raises(CoordError, match="no detail line matches --supersedes exactly"):
        _note({"supersedes": "1. connect desk", "note": "x"})
    assert card["writes"] == 0


def test_two_matches_are_refused(card, monkeypatch):
    card["body"] = json.dumps({"slug": "c333", "doing": "", "detail": "same\nother\nsame"})
    with pytest.raises(CoordError, match="2 detail lines match"):
        _note({"supersedes": "same", "note": "x"})
    assert card["writes"] == 0


def test_needs_new_text(card):
    with pytest.raises(CoordError, match="--supersedes needs the new text"):
        _note({"supersedes": "Steps:"})
    with pytest.raises(CoordError, match="--supersedes needs the new text"):
        _note({"supersedes": "Steps:", "text": "75%"})
    assert card["writes"] == 0


def test_not_with_replace(card):
    with pytest.raises(CoordError, match="not with --replace"):
        _note({"supersedes": "Steps:", "note": "x", "replace": True})


def test_superseded_line_cannot_be_superseded_again(card):
    _note({"supersedes": "Steps:", "note": "Steps v2"})
    with pytest.raises(CoordError, match="already superseded"):
        _note({"supersedes": "[superseded] Steps:", "note": "Steps v3"})
    _note({"supersedes": "Steps v2", "note": "Steps v3"})
    assert _detail(card).startswith("[superseded] Steps:\n[superseded] Steps v2\nSteps v3\n")


def test_plain_note_still_appends(card):
    r = _note({"note": "later"}, who="w1")
    assert _detail(card) == DETAIL + "\nlater"
    assert "superseded" not in r


def test_cli_sends_supersedes(monkeypatch):
    from agent_coord.__main__ import _build_parser
    from agent_coord.client import outbound

    monkeypatch.setattr("agent_coord.client.tokens.resolve_desk_owner", lambda _x="": "asker-desk")
    a = _build_parser().parse_args(
        ["note", "cold-test", "c333", "--supersedes", "1. old", "--note", "1. new"]
    )
    body = outbound.body_from_args(a)
    assert body["supersedes"] == "1. old" and body["note"] == "1. new"


@pytest.mark.parametrize("blank", ["", "   "])
@pytest.mark.parametrize("replace", [False, True])
def test_blank_old_line_is_refused_not_a_plain_note(card, blank, replace):
    with pytest.raises(CoordError, match="--supersedes needs the old line"):
        _note({"supersedes": blank, "note": "x", "replace": replace})
    assert card["writes"] == 0


def test_refusals_never_echo_the_old_line(card):
    secret = "ghp_" + "A" * 36
    with pytest.raises(CoordError) as ei:
        _note({"supersedes": secret, "note": "x"})
    assert secret not in str(ei.value)
    card["body"] = json.dumps({"slug": "c333", "doing": "", "detail": secret + "\n" + secret})
    with pytest.raises(CoordError) as ei:
        _note({"supersedes": secret, "note": "x"})
    assert secret not in str(ei.value)


def test_kept_line_keeps_its_spaces(card):
    card["body"] = json.dumps({"slug": "c333", "doing": "", "detail": "Steps:\n  - step one  \nend"})
    _note({"supersedes": "- step one", "note": "  - step one, fixed"})
    assert _detail(card) == "Steps:\n[superseded]   - step one  \n- step one, fixed\nend"


@pytest.mark.parametrize("blank", ["", "  "])
def test_cli_refuses_a_blank_old_line(monkeypatch, blank):
    from agent_coord.__main__ import _build_parser
    from agent_coord.client import outbound

    monkeypatch.setattr("agent_coord.client.tokens.resolve_desk_owner", lambda _x="": "asker-desk")
    a = _build_parser().parse_args(
        ["note", "cold-test", "c333", "--supersedes", blank, "--note", "x"]
    )
    with pytest.raises(CoordError, match="--supersedes needs the old line"):
        outbound.body_from_args(a)


def test_cli_plain_note_sends_no_supersedes(monkeypatch):
    from agent_coord.__main__ import _build_parser
    from agent_coord.client import outbound

    monkeypatch.setattr("agent_coord.client.tokens.resolve_desk_owner", lambda _x="": "asker-desk")
    for argv in (["note", "cold-test", "c333", "3/9"], ["note", "cold-test", "c333", "--note", "x"]):
        body = outbound.body_from_args(_build_parser().parse_args(argv))
        assert "supersedes" not in body
