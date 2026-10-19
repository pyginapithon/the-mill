# -*- coding: utf-8 -*-
from agent_coord.helpers.errors import CoordError
from agent_coord.server.admin import catalog as admin_cat
from agent_coord.server.admin.guard import require_admin
from agent_coord.server.api.mill.rpc import dispatch



import pytest


@pytest.fixture(autouse=True)
def _ws_gate_noop_for_non_ws_tests(monkeypatch):
    """These modules test Bearer/handlers, not Hub /ws. Sit is enforced in test_ws_gate_verbs."""
    monkeypatch.setattr(
        "agent_coord.server.api.mill.rpc._require_live_ws",
        lambda owner: None,
    )


class Fake:
    _tokens = {}
    _cn = object()

    def resolve_bearer(self, token: str) -> str:
        return "admin-desk" if token else ""

    def _guard_owner(self, *a, **k):
        return {}


def test_require_admin_rejects(monkeypatch):
    monkeypatch.setattr(
        "agent_coord.server.admin.guard.is_role_admin", lambda cn, desk: False
    )
    try:
        require_admin(object(), "desk")
        raise AssertionError("expected CoordError")
    except CoordError as e:
        assert "Admin" in str(e)


def test_dispatch_roster_requires_admin(monkeypatch):
    monkeypatch.setenv("AGENT_COORD_TRUST", "limited")
    monkeypatch.setattr(
        "agent_coord.server.admin.guard.is_role_admin", lambda cn, desk: False
    )
    try:
        dispatch(
            Fake(),
            {
                "verb": "roster",
                "project": "the-mill",
                "owner": "desk",
                "slug": "foo",
                "confirm": "foo",
                "yes": True,
            },
            token="t",
        )
        raise AssertionError("expected CoordError")
    except CoordError as e:
        assert "Admin" in str(e)


def test_dispatch_roster_admin_put(monkeypatch):
    monkeypatch.setattr(
        "agent_coord.server.admin.guard.is_role_admin", lambda cn, desk: True
    )
    monkeypatch.setattr(
        "agent_coord.server.records.name.host_put",
        lambda cn, name, kind="": [{"id": 9, "name": name, "op": "created"}],
    )
    monkeypatch.setattr("agent_coord.server.records.name.get", lambda *a, **k: None)
    rec = dispatch(
        Fake(),
        {
            "verb": "roster",
            "project": "the-mill",
            "owner": "admin-desk",
            "slug": "unit",
            "confirm": "unit",
            "yes": True,
        },
        token="t",
    )
    assert rec and rec[0]["op"] == "created"


def test_dispatch_group_and_role_verbs_are_gone(monkeypatch):
    """0.7.0 hard break: mill roster is the only roster mint verb."""
    monkeypatch.setattr("agent_coord.server.admin.guard.is_role_admin", lambda cn, desk: True)
    for verb in ("group", "role"):
        try:
            dispatch(Fake(), {"verb": verb, "project": "the-mill", "owner": "a", "slug": "u",
                              "confirm": "u", "yes": True}, token="t")
            raise AssertionError("expected CoordError for " + verb)
        except CoordError:
            pass


def test_catalog_slug_mismatch():
    try:
        admin_cat._match("a", "b", verb="roster")
        raise AssertionError("expected CoordError")
    except CoordError:
        pass
