"""claim on a card another desk holds is refused unless --take-over (#325)."""
from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from agent_coord.helpers.errors import CoordError
from agent_coord.server.api.mill import rpc


def _card(monkeypatch, volunteer: str, detail: str = "seed"):
    state = {
        "row": {
            "id": 325,
            "status": "claimed" if volunteer else "open",
            "assigned": volunteer,
            "body": json.dumps({"slug": "c325", "doing": "", "detail": detail}),
        },
        "updates": [],
    }

    def fake_find(cn, project, need):
        return dict(state["row"])

    def fake_update(cn, tid, desk, status="", volunteer="", body=None):
        state["updates"].append({"status": status, "volunteer": volunteer, "body": body})
        if volunteer:
            state["row"]["assigned"] = volunteer
        if body is not None:
            state["row"]["body"] = body
        return [{"id": tid}]

    monkeypatch.setattr("agent_coord.server.records.todo.find", fake_find)
    monkeypatch.setattr("agent_coord.server.records.todo.update", fake_update)
    monkeypatch.setattr(rpc, "_poke", lambda *a, **k: None)
    return state


def test_claim_on_card_held_by_another_desk_is_refused_and_names_holder(monkeypatch):
    state = _card(monkeypatch, "h1-w3")
    with pytest.raises(CoordError) as exc:
        rpc._h_claim(MagicMock(), {"need": "c325"}, "cold-test", "h1-w1")
    msg = str(exc.value)
    assert "claimed by h1-w3" in msg
    assert "mill unclaim cold-test c325" in msg
    assert "--take-over" in msg
    assert state["updates"] == []
    assert state["row"]["assigned"] == "h1-w3"


def test_claim_with_msg_on_held_card_writes_nothing(monkeypatch):
    state = _card(monkeypatch, "h1-w3")
    with pytest.raises(CoordError, match="claimed by h1-w3"):
        rpc._h_claim(MagicMock(), {"need": "c325", "msg": "mine now", "eta": "2h"}, "cold-test", "h1-w1")
    assert state["updates"] == []


def test_take_over_moves_card_and_records_prior_volunteer(monkeypatch):
    state = _card(monkeypatch, "h1-w3")
    out = rpc._h_claim(MagicMock(), {"need": "c325", "take_over": True}, "cold-test", "h1-w1")
    assert out["volunteer"] == "h1-w1"
    assert out["prior_volunteer"] == "h1-w3"
    assert state["row"]["assigned"] == "h1-w1"
    detail = json.loads(state["row"]["body"])["detail"]
    assert detail.startswith("seed\n")
    assert "took over from h1-w3" in detail


def test_reclaim_by_same_desk_still_works(monkeypatch):
    state = _card(monkeypatch, "h1-w1")
    out = rpc._h_claim(MagicMock(), {"need": "c325", "eta": "2h"}, "cold-test", "h1-w1")
    assert out["volunteer"] == "h1-w1"
    assert "prior_volunteer" not in out
    assert len(state["updates"]) == 1


def test_claim_of_unclaimed_card_is_unchanged(monkeypatch):
    state = _card(monkeypatch, "")
    out = rpc._h_claim(MagicMock(), {"need": "c325"}, "cold-test", "h1-w1")
    assert out["status"] == "claimed" and out["volunteer"] == "h1-w1"
    assert "prior_volunteer" not in out
    assert state["updates"][0]["body"] is None


def test_take_over_on_free_card_records_nothing_extra(monkeypatch):
    state = _card(monkeypatch, "")
    out = rpc._h_claim(MagicMock(), {"need": "c325", "take_over": True}, "cold-test", "h1-w1")
    assert "prior_volunteer" not in out
    assert state["updates"][0]["body"] is None


def test_cli_claim_take_over_flag_reaches_body(monkeypatch):
    from agent_coord.__main__ import _build_parser as build_parser
    from agent_coord.client import outbound

    monkeypatch.setattr("agent_coord.client.tokens.resolve_desk_owner", lambda _x: "h1-w1")
    args = build_parser().parse_args(["claim", "cold-test", "c325", "--take-over"])
    body = outbound.body_from_args(args)
    assert body["take_over"] is True
    plain = outbound.body_from_args(build_parser().parse_args(["claim", "cold-test", "c325"]))
    assert "take_over" not in plain
