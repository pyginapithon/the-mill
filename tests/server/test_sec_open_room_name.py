# -*- coding: utf-8 -*-
"""Security: only a named room is open-join by reply (#sec S-3)."""
from __future__ import annotations

import secrets

import pytest

from agent_coord.server.api.mill import rpc


@pytest.mark.parametrize("name", ["agent-ux", "priors-review", "f20-room", "build"])
def test_named_room_is_open(name):
    assert rpc._open_room(name) is True


def test_room_opened_by_reply_is_private():
    assert rpc._open_room(secrets.token_hex(5)) is False


@pytest.mark.parametrize("name", ["", "  "])
def test_off_tree_is_not_an_open_room(name):
    assert rpc._open_room(name) is False
