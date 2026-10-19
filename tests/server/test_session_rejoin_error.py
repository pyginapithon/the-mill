"""Invalid/expired Bearer must tell desks to rejoin."""
from __future__ import annotations

import pytest

from agent_coord.client.session_errors import (
    SESSION_INVALID_REJOIN,
    SESSION_TOKEN_REQUIRED,
)
from agent_coord.helpers.errors import CoordError
from agent_coord.server.api.mill import rpc



@pytest.fixture(autouse=True)
def _ws_gate_noop_for_non_ws_tests(monkeypatch):
    """These modules test Bearer/handlers, not Hub /ws. Sit is enforced in test_ws_gate_verbs."""
    monkeypatch.setattr(
        "agent_coord.server.api.mill.rpc._require_live_ws",
        lambda owner: None,
    )


class _FakeBook:
    def resolve_bearer(self, token: str) -> str:
        return ""  # wiped hash / unknown

    def _guard_owner(self, *a, **k):
        raise AssertionError("should not guard when bearer empty")


def test_session_invalid_rejoin_copy_is_plain_ascii():
    SESSION_INVALID_REJOIN.encode("cp1252")
    SESSION_TOKEN_REQUIRED.encode("cp1252")
    assert "rejoin" in SESSION_INVALID_REJOIN.lower()
    assert "invalid" in SESSION_INVALID_REJOIN.lower() or "expired" in SESSION_INVALID_REJOIN.lower()


def test_dispatch_unknown_bearer_says_rejoin():
    with pytest.raises(CoordError) as ei:
        rpc.dispatch(_FakeBook(), {"verb": "todo", "project": "the-mill"}, token="stale-token")
    assert str(ei.value) == SESSION_INVALID_REJOIN


def test_dispatch_missing_token_required_message():
    with pytest.raises(CoordError) as ei:
        rpc.dispatch(_FakeBook(), {"verb": "todo", "project": "the-mill"}, token="")
    assert str(ei.value) == SESSION_TOKEN_REQUIRED
