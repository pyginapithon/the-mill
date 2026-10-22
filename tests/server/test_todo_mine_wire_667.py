"""#667: todo --mine is filtered on the wall, not after the whole board crossed the wire (F83)."""
from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from agent_coord.server.api.mill import rpc
from agent_coord.server.book import Book


def _row(i: int, roster: str, assigned: str, labels: list[str] | None = None) -> dict:
    return {
        "id": i,
        "status": "claimed" if assigned else "open",
        "roster": roster,
        "body": json.dumps({"slug": "c%d" % i, "detail": "x" * 2000}),
        "assigned": assigned,
        "creator": "ask",
        "labels": json.dumps(labels or []),
    }


ROWS = [
    _row(1, "the-mill", "me"),
    _row(2, "the-mill", "other"),
    _row(3, "agent-ux", "", ["me"]),
    _row(4, "agent-ux", "other", ["bug"]),
    _row(5, "the-mill", ""),
]


def _many(body: dict, owner: str = "me") -> dict:
    c = MagicMock(spec=Book)
    c._cn = MagicMock()
    with patch("agent_coord.server.records.todo.page", return_value=list(ROWS)):
        return rpc._h_todo(c, dict(body, rosters=["the-mill", "agent-ux"]), "the-mill", owner)


def test_mine_read_carries_only_the_desks_cards() -> None:
    out = _many({"mine": True})
    assert sorted(c["id"] for c in out["cards"]) == [1, 3]


def test_mine_read_is_far_smaller_than_the_board() -> None:
    board = len(json.dumps(_many({})))
    mine = len(json.dumps(_many({"mine": True})))
    assert mine * 2 < board


def test_plain_board_is_unchanged() -> None:
    assert sorted(c["id"] for c in _many({})["cards"]) == [1, 2, 3, 4, 5]


def test_cli_body_asks_the_wall_for_mine() -> None:
    from agent_coord.client.outbound import body_from_args

    args = SimpleNamespace(cmd="todo", project="", need="", mine=True, all=False, done=False, fixtures=False)
    with patch("agent_coord.client.tokens.resolve_desk_owner", return_value="me"):
        body = body_from_args(args)
    assert body.get("mine") is True
