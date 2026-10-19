"""records/join.py human badges (old mill presence)."""
from __future__ import annotations

import pytest

from agent_coord.server.records.join import (
    STABLE_HUMANS,
    is_stable_human,
)


def test_no_hardcoded_session_roles_070():
    """0.7.0: rosters are data; there is no hardcoded role list."""
    from agent_coord.helpers import ident

    assert not hasattr(ident, "SESSION_ROLES")
    assert not hasattr(ident, "is_session_role")


@pytest.mark.parametrize(
    "owner, expect",
    [
        ("setter-upper", True),
        ("human", True),
        ("desk.setter-upper", False),
        ("desk.human", False),
        (" human ", True),
        ("builder", False),
        ("app-desk", False),
        ("", False),
        (None, False),
        ("desk.app-desk", False),
    ],
)
def test_is_stable_human(owner, expect):
    assert is_stable_human(owner) is expect


def test_stable_humans_frozen_contents():
    assert STABLE_HUMANS == frozenset({"setter-upper", "human"})
