# -*- coding: utf-8 -*-
"""Security: /api/admin/invites authenticates from the session or bearer (#sec S-4).

A body `owner` string is never proof of identity. A door-mutating action (mint,
revoke, ttl, door, network, ...) and mint_seat require either a bearer that
resolves to an Admin desk or a signed-in human whose role is Admin.
"""
from __future__ import annotations

import pytest

from agent_coord.helpers.errors import CoordError
from agent_coord.server.admin import invites as inv


class C:
    _cn = object()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _office():
    return C()


# --- core repro: naming an Admin desk with no credential is refused ---

def test_mint_refuses_body_owner_without_credential(monkeypatch):
    # Pre-fix this minted because the body owner named an Admin desk.
    monkeypatch.setattr(inv, "is_role_admin", lambda _cn, d: d == "DESK_admin")
    monkeypatch.setattr("agent_coord.server.admin.door.mint_key", lambda **k: {"ok": True, "key_id": "X"})
    with pytest.raises(CoordError) as ei:
        inv.post_invites({"action": "mint", "owner": "DESK_admin"}, office=_office)
    assert "not proof" in str(ei.value).lower()


def test_revoke_refuses_body_owner_without_credential(monkeypatch):
    monkeypatch.setattr(inv, "is_role_admin", lambda _cn, d: d == "DESK_admin")
    monkeypatch.setattr("agent_coord.server.admin.door.revoke_key", lambda *a, **k: {"ok": True})
    with pytest.raises(CoordError):
        inv.post_invites(
            {"action": "revoke", "owner": "DESK_admin", "key_id": "k1"}, office=_office
        )


def test_door_set_refuses_body_owner_without_credential(monkeypatch):
    monkeypatch.setattr(inv, "is_role_admin", lambda _cn, d: d == "DESK_admin")
    monkeypatch.setattr("agent_coord.server.admin.door.set_door", lambda *a, **k: {"ok": True})
    with pytest.raises(CoordError):
        inv.post_invites(
            {"action": "door", "owner": "DESK_admin", "door": "invite"}, office=_office
        )


# --- positive: a verified Admin bearer mints ---

def test_mint_allows_admin_desk_bearer(monkeypatch):
    monkeypatch.setattr(
        "agent_coord.server.records.join.desk_for_token_hash",
        lambda _cn, _h: "DESK_admin",
    )
    monkeypatch.setattr(inv, "is_role_admin", lambda _cn, d: d == "DESK_admin")
    monkeypatch.setattr(
        "agent_coord.server.admin.door.mint_key", lambda **k: {"ok": True, "key_id": "X"}
    )
    row = inv.post_invites(
        {"action": "mint", "token": "admin-seat-token"}, office=_office
    )
    assert row["ok"] is True and row["key_id"] == "X"


def test_mint_allows_verified_signed_in_human(monkeypatch):
    monkeypatch.setattr(
        "agent_coord.server.records.join.desk_for_token_hash", lambda _cn, _h: ""
    )
    monkeypatch.setattr(inv, "_human_bearer_ok", lambda _cn, t: t == "human-cookie")
    monkeypatch.setattr(inv, "is_human_admin", lambda _cn, _h: True)
    monkeypatch.setattr(
        "agent_coord.server.admin.door.mint_key", lambda **k: {"ok": True, "key_id": "Y"}
    )
    row = inv.post_invites(
        {"action": "mint"}, office=_office, human_token="human-cookie"
    )
    assert row["ok"] is True and row["key_id"] == "Y"


# --- edges: a credential that is real but not Admin is refused ---

def test_mint_refuses_signed_in_viewer_human(monkeypatch):
    monkeypatch.setattr(
        "agent_coord.server.records.join.desk_for_token_hash", lambda _cn, _h: ""
    )
    monkeypatch.setattr(inv, "_human_bearer_ok", lambda _cn, t: t == "human-cookie")
    monkeypatch.setattr(inv, "is_human_admin", lambda _cn, _h: False)
    monkeypatch.setattr(
        "agent_coord.server.admin.door.mint_key", lambda **k: {"ok": True, "key_id": "Y"}
    )
    with pytest.raises(CoordError):
        inv.post_invites({"action": "mint"}, office=_office, human_token="human-cookie")


def test_mint_refuses_non_admin_desk_bearer_naming_admin_owner(monkeypatch):
    monkeypatch.setattr(
        "agent_coord.server.records.join.desk_for_token_hash", lambda _cn, _h: "DESK_plain"
    )
    monkeypatch.setattr(inv, "is_role_admin", lambda _cn, d: d == "DESK_admin")
    monkeypatch.setattr(inv, "_human_bearer_ok", lambda *a, **k: False)
    monkeypatch.setattr(
        "agent_coord.server.admin.door.mint_key", lambda **k: {"ok": True, "key_id": "X"}
    )
    with pytest.raises(CoordError):
        inv.post_invites(
            {"action": "mint", "owner": "DESK_admin", "token": "plain-seat"}, office=_office
        )


@pytest.mark.parametrize("action", ["ttl", "join", "network"])
def test_other_mutations_refuse_body_owner_without_credential(monkeypatch, action):
    monkeypatch.setattr(inv, "is_role_admin", lambda _cn, d: d == "DESK_admin")
    for fn in ("set_key_ttl", "record_join"):
        monkeypatch.setattr(f"agent_coord.server.admin.door.{fn}", lambda *a, **k: True)
    monkeypatch.setattr("agent_coord.server.netbind.set_lan_only", lambda *a, **k: {"ok": True})
    with pytest.raises(CoordError):
        inv.post_invites(
            {"action": action, "owner": "DESK_admin", "key_id": "k1", "lan_only": True},
            office=_office,
        )


# --- mint_seat: same identity rule ---

def test_mint_seat_refuses_body_owner_without_credential(monkeypatch):
    # Admin check must run on the proven desk, not the body owner.
    monkeypatch.setattr(
        "agent_coord.server.admin.guard.is_role_admin", lambda _cn, d: d == "DESK_admin"
    )
    monkeypatch.setattr("agent_coord.config.mill_trust", lambda: "limited")
    monkeypatch.setattr(
        "agent_coord.server.records.join.desk_for_token_hash", lambda _cn, _h: ""
    )
    monkeypatch.setattr(inv, "_human_token_ok", lambda *a, **k: False)
    monkeypatch.setattr(inv, "_human_bearer_ok", lambda *a, **k: False)
    monkeypatch.setattr(
        "agent_coord.server.admin.seats.resolve_seat_roster",
        lambda cn, desk, wanted="": wanted or "the-mill",
    )
    monkeypatch.setattr(
        "agent_coord.server.admin.seats.mint_seat", lambda cn, **k: {"ok": True, "desk": "bot"}
    )
    with pytest.raises(CoordError):
        inv.post_invites(
            {"action": "mint_seat", "owner": "DESK_admin", "desk": "bot"}, office=_office
        )


def test_mint_seat_allows_admin_desk_bearer(monkeypatch):
    monkeypatch.setattr(
        "agent_coord.server.records.join.desk_for_token_hash",
        lambda _cn, _h: "DESK_admin",
    )
    monkeypatch.setattr(
        "agent_coord.server.admin.guard.is_role_admin", lambda _cn, d: d == "DESK_admin"
    )
    monkeypatch.setattr(inv, "is_role_admin", lambda _cn, d: d == "DESK_admin")
    monkeypatch.setattr(inv, "_human_token_ok", lambda *a, **k: False)
    monkeypatch.setattr(inv, "_human_bearer_ok", lambda *a, **k: False)
    monkeypatch.setattr(
        "agent_coord.server.admin.seats.resolve_seat_roster",
        lambda cn, desk, wanted="": wanted or "the-mill",
    )
    monkeypatch.setattr(
        "agent_coord.server.admin.seats.mint_seat",
        lambda cn, **k: {"ok": True, "desk": "bot", "seat": "S", "invite_url": "https://w/welcome"},
    )
    row = inv.post_invites(
        {"action": "mint_seat", "token": "admin-seat", "desk": "bot"}, office=_office
    )
    assert row["ok"] is True and row["desk"] == "bot"


# --- #sec S-5: the read-only list takes the same Admin check ---

def _board(monkeypatch):
    monkeypatch.setattr(
        "agent_coord.server.admin.door.board_packet",
        lambda: {"door": "invite", "keys": [{"key_id": "K1", "created_by": "DESK_admin"}]},
    )


@pytest.mark.parametrize("action", ["list", "board", ""])
def test_list_action_refuses_body_owner_without_credential(monkeypatch, action):
    _board(monkeypatch)
    monkeypatch.setattr(inv, "is_role_admin", lambda _cn, d: d == "DESK_admin")
    with pytest.raises(CoordError) as ei:
        inv.post_invites({"action": action, "owner": "DESK_admin"}, office=_office)
    assert "not proof" in str(ei.value).lower()


def test_get_list_refuses_no_credential(monkeypatch):
    _board(monkeypatch)
    with pytest.raises(CoordError):
        inv.list_invites(office=_office)


def test_get_list_refuses_non_admin_desk_bearer(monkeypatch):
    _board(monkeypatch)
    monkeypatch.setattr(
        "agent_coord.server.records.join.desk_for_token_hash", lambda _cn, _h: "DESK_worker"
    )
    monkeypatch.setattr(inv, "is_role_admin", lambda _cn, d: d == "DESK_admin")
    monkeypatch.setattr(inv, "_human_bearer_ok", lambda *a, **k: False)
    with pytest.raises(CoordError):
        inv.list_invites(office=_office, token="worker-seat-token")


def test_get_list_refuses_signed_in_viewer_human(monkeypatch):
    _board(monkeypatch)
    monkeypatch.setattr(
        "agent_coord.server.records.join.desk_for_token_hash", lambda _cn, _h: ""
    )
    monkeypatch.setattr(inv, "_human_bearer_ok", lambda _cn, t: t == "human-cookie")
    monkeypatch.setattr(inv, "is_human_admin", lambda _cn, _h: False)
    with pytest.raises(CoordError):
        inv.list_invites(office=_office, session="human-cookie")


def test_get_list_allows_admin_desk_bearer(monkeypatch):
    _board(monkeypatch)
    monkeypatch.setattr(
        "agent_coord.server.records.join.desk_for_token_hash", lambda _cn, _h: "DESK_admin"
    )
    monkeypatch.setattr(inv, "is_role_admin", lambda _cn, d: d == "DESK_admin")
    row = inv.list_invites(office=_office, token="admin-seat-token")
    assert row["keys"][0]["key_id"] == "K1"


def test_get_list_allows_signed_in_admin_human(monkeypatch):
    _board(monkeypatch)
    monkeypatch.setattr(
        "agent_coord.server.records.join.desk_for_token_hash", lambda _cn, _h: ""
    )
    monkeypatch.setattr(inv, "_human_bearer_ok", lambda _cn, t: t == "human-cookie")
    monkeypatch.setattr(inv, "is_human_admin", lambda _cn, _h: True)
    row = inv.list_invites(office=_office, session="human-cookie")
    assert row["door"] == "invite"


def test_http_get_route_uses_the_admin_list():
    from pathlib import Path

    src = (Path(inv.__file__).resolve().parents[1] / "middleware.py").read_text(encoding="utf-8")
    at = src.index('if path in ("/api/admin/invites", "/api/invites"):')
    route = src[at : at + 900]
    assert "list_invites(" in route and "import board" not in route
    assert "403" in route
