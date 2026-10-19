# -*- coding: utf-8 -*-
"""Security: a signed-in human is an Admin only by role (#sec S-4).

is_human_admin gates door-mutating /api/admin/invites actions for a human
bearer. A human with no role row is a viewer and is not an Admin.
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.sql

from agent_coord.client.tokens import token_hash
from agent_coord.const import CONST_ADMIN, CONST_ROSTER
from agent_coord.server.admin.guard import is_human_admin
from agent_coord.server.records import human as rec_human
from tests.server.records.conftest import seed_names


def test_human_with_admin_role_is_admin(cn):
    seed_names(cn, (CONST_ADMIN, CONST_ROSTER))
    rec_human.put(cn, token_hash("bearer-admin"), "sub-admin", CONST_ADMIN)
    assert is_human_admin(cn, token_hash("bearer-admin")) is True


def test_human_without_role_is_viewer_not_admin(cn):
    seed_names(cn, (CONST_ADMIN, CONST_ROSTER))
    rec_human.put(cn, token_hash("bearer-viewer"), "sub-viewer", "")
    assert is_human_admin(cn, token_hash("bearer-viewer")) is False


def test_unknown_bearer_is_not_admin(cn):
    seed_names(cn, (CONST_ADMIN, CONST_ROSTER))
    assert is_human_admin(cn, token_hash("bearer-unknown")) is False
    assert is_human_admin(cn, "") is False
