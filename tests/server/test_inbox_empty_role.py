"""#47 mill inbox must not slug empty role -> bad id: ''."""
from __future__ import annotations

import pytest

from unittest.mock import MagicMock, patch

from agent_coord.helpers.errors import CoordError
from agent_coord.server.api.mill import rpc
from agent_coord.server.book import Book



@pytest.fixture(autouse=True)
def _ws_gate_noop_for_non_ws_tests(monkeypatch):
    """These modules test Bearer/handlers, not Hub /ws. Sit is enforced in test_ws_gate_verbs."""
    monkeypatch.setattr(
        "agent_coord.server.api.mill.rpc._require_live_ws",
        lambda owner: None,
    )


def test_inbox_empty_role_ok():
    c = MagicMock(spec=Book)
    c._cn = MagicMock()
    body = {"dst": "grok-tui", "no_mark": True, "limit": 3}
    with patch("agent_coord.server.records.mail.inbox", return_value=[]) as sel:
        out = rpc._h_inbox(c, body, "the-mill", "grok-tui")
    assert out == []
    args = sel.call_args[0]
    assert len(args) == 2
    assert args[1]


def test_inbox_missing_dest_errors():
    c = MagicMock(spec=Book)
    c._cn = MagicMock()
    with patch("agent_coord.server.records.mail.inbox", return_value=[]):
        try:
            rpc._h_inbox(c, {"no_mark": True}, "the-mill", None)
        except CoordError as e:
            assert "owner" in str(e).lower()
        else:
            raise AssertionError("expected CoordError")


def test_dispatch_empty_owner_is_owner_required_not_bad_id():
    c = MagicMock(spec=Book)
    c._tokens = {}
    try:
        rpc.dispatch(c, {"verb": "inbox", "project": "the-mill", "dst": "grok-tui"}, token="x")
    except CoordError as e:
        assert "bad id" not in str(e).lower()
        assert "bearer" in str(e).lower() or "dest" in str(e).lower()
    else:
        raise AssertionError("expected CoordError")
