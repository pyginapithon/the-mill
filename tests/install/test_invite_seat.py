# -*- coding: utf-8 -*-
"""One-seat agent invite mint: trust gate + URL shape + CLI verb."""
from __future__ import annotations

from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

import pytest

from agent_coord.helpers.errors import CoordError


def test_invite_url_shape() -> None:
    from agent_coord.server.admin.seats import invite_url_for

    url = invite_url_for(desk="bot-a", seat="sekret_once", base="https://wall.example")
    assert url.startswith("https://wall.example/welcome?")
    q = parse_qs(urlparse(url).query)
    assert q["desk"] == ["bot-a"]
    assert q["seat"] == ["sekret_once"]
    same = invite_url_for(desk="bot-a", seat="sekret_once", base="https://wall.example")
    assert parse_qs(urlparse(same).query)["desk"] == ["bot-a"]


def test_gate_admin_always(monkeypatch) -> None:
    from agent_coord.server.admin import guard

    monkeypatch.setattr(guard, "is_role_admin", lambda _cn, _d: True)
    monkeypatch.setattr("agent_coord.config.mill_trust", lambda: "limited")
    guard.require_invite_seat_mint(object(), "DESK_admin", human_ok=False)


def test_gate_human_high_ok(monkeypatch) -> None:
    from agent_coord.server.admin import guard

    monkeypatch.setattr(guard, "is_role_admin", lambda _cn, _d: False)
    monkeypatch.setattr("agent_coord.config.mill_trust", lambda: "high")
    guard.require_invite_seat_mint(object(), "DESK_human", human_ok=True)


def test_gate_human_limited_refuses(monkeypatch) -> None:
    from agent_coord.server.admin import guard

    monkeypatch.setattr(guard, "is_role_admin", lambda _cn, _d: False)
    monkeypatch.setattr("agent_coord.config.mill_trust", lambda: "limited")
    with pytest.raises(CoordError) as ei:
        guard.require_invite_seat_mint(object(), "DESK_human", human_ok=True)
    assert str(ei.value) == "limited-trust: mint_seat needs roster Admin"


def test_gate_non_admin_agent_high_refuses(monkeypatch) -> None:
    from agent_coord.server.admin import guard

    monkeypatch.setattr(guard, "is_role_admin", lambda _cn, _d: False)
    monkeypatch.setattr("agent_coord.config.mill_trust", lambda: "high")
    with pytest.raises(CoordError) as ei:
        guard.require_invite_seat_mint(object(), "alice", human_ok=False)
    assert str(ei.value) == "mint_seat: roster Admin or (trust=high) human badge"


def test_h_invite_seat_refuses_non_admin(monkeypatch) -> None:
    from agent_coord.server.api.mill.rpc import _h_invite_seat

    class Book:
        _cn = object()

    def deny(_cn, _desk, *, human_ok=False):
        raise CoordError("mint_seat: roster Admin or (trust=high) human badge")

    monkeypatch.setattr(
        "agent_coord.server.admin.guard.require_invite_seat_mint", deny
    )
    with pytest.raises(CoordError) as ei:
        _h_invite_seat(Book(), {"desk": "bot1"}, "the-mill", "DESK_alice")
    assert str(ei.value) == "mint_seat: roster Admin or (trust=high) human badge"


def test_h_invite_seat_mints(monkeypatch) -> None:
    from agent_coord.server.api.mill.rpc import _h_invite_seat

    class Book:
        _cn = object()

    seen: dict = {}

    def allow(_cn, _desk, *, human_ok=False):
        return None

    def fake_mint(cn, *, desk, project="the-mill", created_by="", doing="invited", mill_url=None):
        seen.update(desk=desk, project=project, created_by=created_by)
        return {
            "ok": True,
            "desk": desk[5:] if desk.startswith("DESK_") else desk,
            "seat": "ONCE",
            "invite_url": "https://wall.example/welcome?desk=bot1&seat=ONCE",
            "status": "ready",
        }

    monkeypatch.setattr(
        "agent_coord.server.admin.guard.require_invite_seat_mint", allow
    )
    monkeypatch.setattr("agent_coord.server.admin.seats.mint_seat", fake_mint)
    # Patch import path used inside handler
    import agent_coord.server.admin.seats as seats_mod

    monkeypatch.setattr(seats_mod, "mint_seat", fake_mint)
    # Patch live-project check used by the handler (#252).
    monkeypatch.setattr(
        "agent_coord.server.api.mill.rpc._require_live_project",
        lambda cn, name, verb: name,
    )
    row = _h_invite_seat(
        Book(), {"desk": "bot1", "project": "the-mill"}, "Office", "DESK_admin"
    )
    assert row["ok"] is True
    assert row["seat"] == "ONCE"
    assert row["status"] == "ready"
    assert "/welcome?" in row["invite_url"]
    assert "desk=bot1" in row["invite_url"]
    assert "DESK_" not in row["invite_url"]
    assert row["desk"] == "bot1"
    assert "seat=ONCE" in row["invite_url"]
    assert seen["desk"] == "bot1"
    assert seen["project"] == "the-mill"  # body --project, not connect Office


def test_post_invites_mint_seat_human_high(monkeypatch) -> None:
    from agent_coord.server.admin import invites as inv

    class C:
        _cn = object()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(inv, "_human_token_ok", lambda *_a, **_k: True)
    monkeypatch.setattr(inv, "require_invite_seat_mint", lambda *_a, **_k: None)

    def fake_mint(cn, **kw):
        return {
            "ok": True,
            "desk": "bot2",
            "seat": "S2",
            "invite_url": "https://w/welcome?desk=bot2&seat=S2",
            "status": "ready",
        }

    monkeypatch.setattr("agent_coord.server.admin.seats.mint_seat", fake_mint)
    monkeypatch.setattr(
        "agent_coord.server.admin.seats.resolve_seat_roster",
        lambda cn, desk, wanted="": wanted or "the-mill",
    )
    row = inv.post_invites(
        {
            "action": "mint_seat",
            "owner": "DESK_human",
            "token": "badge",
            "desk": "bot2",
            "project": "the-mill",
        },
        office=lambda: C(),
    )
    assert row["invite_url"].startswith("https://")
    assert row["desk"] == "bot2"
    assert row["seat"] == "S2"


def test_cli_invite_seat_posts_invite_seat_verb(monkeypatch, capsys) -> None:
    from agent_coord.__main__ import _invite_cmd

    seen: dict = {}

    def call(body):
        seen.update(body)
        return {
            "ok": True,
            "desk": "bot3",
            "seat": "S3",
            "invite_url": "https://203.0.113.10/welcome?desk=bot3&seat=S3",
            "status": "ready",
        }

    monkeypatch.setattr("agent_coord.client.http.mill_http_call", call)
    monkeypatch.setattr(
        "agent_coord.client.tokens.resolve_desk_owner",
        lambda _ignored="": "DESK_admin",
    )
    monkeypatch.setattr(
        "agent_coord.client.http.mill_url",
        lambda: "https://203.0.113.10",
    )
    args = SimpleNamespace(
        owner="DESK_admin",
        door="",
        rotate=False,
        mint=False,
        enable="",
        invite_list=False,
        revoke="",
        ttl="",
        ttl_for="",
        label="",
        seat="bot3",
        join="",
        party="human",
        party_id="",
        lan_only=None,
        cmd="invite",
        seat_roster="the-mill",
    )
    rc = _invite_cmd(args)
    out = capsys.readouterr().out
    assert rc == 0
    assert seen["verb"] == "invite-seat"
    assert seen["desk"] == "bot3"
    assert seen["project"] == "the-mill"
    assert "https://203.0.113.10/welcome?desk=bot3&seat=S3" in out
    assert "DESK_bot3" not in out
    assert '"seat"' not in out  # plaintext only on URL line


def test_post_invites_cognito_cookie_mints_on_high(monkeypatch) -> None:
    from agent_coord.server.admin import invites as inv

    class C:
        _cn = object()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(inv, "_human_token_ok", lambda *_a, **_k: False)
    monkeypatch.setattr(inv, "_human_bearer_ok", lambda _cn, token: token == "door-bearer")
    monkeypatch.setattr(
        "agent_coord.server.admin.guard.is_role_admin", lambda *_a, **_k: False
    )
    monkeypatch.setattr("agent_coord.config.mill_trust", lambda: "high")

    def fake_mint(cn, **kw):
        return {
            "ok": True,
            "desk": "agent1",
            "seat": "S",
            "invite_url": "https://wall.example/welcome?desk=agent1&seat=S",
            "status": "ready",
        }

    monkeypatch.setattr("agent_coord.server.admin.seats.mint_seat", fake_mint)
    monkeypatch.setattr(
        "agent_coord.server.admin.seats.resolve_seat_roster",
        lambda cn, desk, wanted="": wanted or "the-mill",
    )
    row = inv.post_invites(
        {"action": "mint_seat", "owner": "builder", "desk": "agent1", "project": "the-mill"},
        office=lambda: C(),
        human_token="door-bearer",
    )
    assert row["invite_url"].startswith("https://")
    assert row["desk"] == "agent1"


def test_post_invites_cognito_cookie_refuses_on_limited(monkeypatch) -> None:
    from agent_coord.server.admin import invites as inv

    class C:
        _cn = object()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(inv, "_human_token_ok", lambda *_a, **_k: False)
    monkeypatch.setattr(inv, "_human_bearer_ok", lambda *_a, **_k: True)
    monkeypatch.setattr(
        "agent_coord.server.admin.guard.is_role_admin", lambda *_a, **_k: False
    )
    monkeypatch.setattr("agent_coord.config.mill_trust", lambda: "limited")
    with pytest.raises(CoordError, match="limited-trust: mint_seat needs roster Admin"):
        inv.post_invites(
            {"action": "mint_seat", "owner": "builder", "desk": "agent1"},
            office=lambda: C(),
            human_token="door-bearer",
        )


def test_seat_count_office_total(monkeypatch) -> None:
    from agent_coord.server.admin import invites as inv

    class C:
        _cn = object()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(inv, "_human_token_ok", lambda *_a, **_k: True)
    monkeypatch.setattr(inv, "require_invite_seat_mint", lambda *_a, **_k: None)
    monkeypatch.setattr(
        "agent_coord.server.admin.seats.seat_count",
        lambda cn: {"ok": True, "invites": 29, "joined": 4},
    )
    row = inv.post_invites(
        {"action": "seat_count", "owner": "DESK_admin", "token": "badge"},
        office=lambda: C(),
    )
    assert row == {"ok": True, "invites": 29, "joined": 4}


def test_invite_count_alias(monkeypatch) -> None:
    from agent_coord.server.admin import invites as inv

    class C:
        _cn = object()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(inv, "_human_token_ok", lambda *_a, **_k: True)
    monkeypatch.setattr(inv, "require_invite_seat_mint", lambda *_a, **_k: None)
    monkeypatch.setattr(
        "agent_coord.server.admin.seats.seat_count",
        lambda cn: {"ok": True, "invites": 1, "joined": 0},
    )
    row = inv.post_invites(
        {"action": "invite_count", "owner": "DESK_admin"},
        office=lambda: C(),
    )
    assert row == {"ok": True, "invites": 1, "joined": 0}


def test_seat_count_gate_rejects(monkeypatch) -> None:
    from agent_coord.server.admin import invites as inv
    from agent_coord.helpers.errors import CoordError

    class C:
        _cn = object()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def deny(_cn, _desk, *, human_ok=False):
        raise CoordError("mint_seat: roster Admin or (trust=high) human badge")

    monkeypatch.setattr(inv, "_human_token_ok", lambda *_a, **_k: False)
    monkeypatch.setattr(inv, "require_invite_seat_mint", deny)
    with pytest.raises(CoordError) as ei:
        inv.post_invites(
            {"action": "seat_count", "owner": "DESK_alice"},
            office=lambda: C(),
        )
    assert str(ei.value) == "mint_seat: roster Admin or (trust=high) human badge"


def test_seat_count_sql_shape() -> None:
    """invites=COUNT(mill_invite); joined=COUNT(mill_invite_join). Not join.token_hash."""
    from agent_coord.server.admin import seats as seats_mod

    class Cur:
        def __init__(self):
            self.sqls: list[str] = []
            self._i = 0

        def execute(self, sql, args=None):
            self.sqls.append(sql)

        def fetchone(self):
            # first query invites=29, second joined=4
            vals = [(29,), (4,)]
            row = vals[self._i]
            self._i += 1
            return row

        def close(self):
            return None

    class Cn:
        def __init__(self):
            self.cur = Cur()

        def cursor(self):
            return self.cur

    cn = Cn()
    row = seats_mod.seat_count(cn)
    assert row == {"ok": True, "invites": 29, "joined": 4}
    assert any("mill_invite" in s and "mill_invite_join" not in s for s in cn.cur.sqls)
    assert any("mill_invite_join" in s for s in cn.cur.sqls)
    assert all("token_hash" not in s for s in cn.cur.sqls)
    assert all("`join`" not in s for s in cn.cur.sqls)


def test_door_mint_and_join_bump_counts() -> None:
    """Door mint bumps invites; mill_invite_join row bumps joined."""
    from agent_coord.server.admin import seats as seats_mod

    invites: list[str] = []
    joins: list[tuple[str, str, str]] = []

    class Cur:
        def __init__(self):
            self.sql = ""

        def execute(self, sql, args=None):
            self.sql = sql

        def fetchone(self):
            if "mill_invite_join" in self.sql:
                return (len(joins),)
            if "mill_invite" in self.sql:
                return (len(invites),)
            return (0,)

        def close(self):
            return None

    class Cn:
        def cursor(self):
            return Cur()

    cn = Cn()
    assert seats_mod.seat_count(cn) == {"ok": True, "invites": 0, "joined": 0}
    # simulate door mint -> INSERT mill_invite
    invites.append("k1")
    assert seats_mod.seat_count(cn)["invites"] == 1
    assert seats_mod.seat_count(cn)["joined"] == 0
    invites.append("k2")
    assert seats_mod.seat_count(cn)["invites"] == 2
    # simulate record_join -> INSERT mill_invite_join
    joins.append(("k1", "human", "alice"))
    assert seats_mod.seat_count(cn) == {"ok": True, "invites": 2, "joined": 1}
    joins.append(("k1", "agent", "bot-a"))
    joins.append(("k2", "human", "bob"))
    assert seats_mod.seat_count(cn) == {"ok": True, "invites": 2, "joined": 3}


def test_mint_seat_unaffected_by_count(monkeypatch) -> None:
    """mint_seat still writes join.token_hash; count path does not touch it."""
    from agent_coord.server.admin import seats as seats_mod

    seen: dict = {}

    def fake_upsert(cn, project, desk, role="", token_hash=None, doing=None):
        seen["token_hash"] = token_hash
        seen["desk"] = desk
        return [{"owner": desk, "desk_id": 1}]

    office: dict = {}

    def put_office(cn, desk):
        office["desk"] = desk

    monkeypatch.setattr("agent_coord.server.records.join.upsert", fake_upsert)
    monkeypatch.setattr("agent_coord.server.records.member.put_office", put_office)
    row = seats_mod.mint_seat(
        object(),
        desk="bot-z",
        created_by="DESK_admin",
        mill_url="https://wall.example",
    )
    assert row["ok"] is True
    assert row["status"] == "ready"
    assert row["desk"] == "bot-z"
    assert seen["token_hash"]  # hash still stored for mint_seat
    assert seen["desk"] == "bot-z"
    assert office["desk"] == "bot-z"
    q = parse_qs(urlparse(row["invite_url"]).query)
    assert q["desk"] == ["bot-z"]


def test_h_invite_seat_defaults_to_desk_membership(monkeypatch) -> None:
    from agent_coord.server.api.mill.rpc import _h_invite_seat

    class Book:
        _cn = object()

    seen: dict = {}

    def fake_mint(cn, *, desk, project="the-mill", created_by="", doing="invited", mill_url=None):
        seen.update(desk=desk, project=project)
        return {"ok": True, "desk": desk, "seat": "S", "invite_url": "u", "status": "ready"}

    monkeypatch.setattr(
        "agent_coord.server.admin.guard.require_invite_seat_mint", lambda *a, **k: None
    )
    monkeypatch.setattr("agent_coord.server.admin.seats.mint_seat", fake_mint)
    monkeypatch.setattr(
        "agent_coord.server.api.mill.rpc._seat_roster", lambda cn, desk: "ops"
    )
    monkeypatch.setattr(
        "agent_coord.server.api.mill.rpc._require_live_project",
        lambda cn, name, verb: name,
    )
    import agent_coord.server.admin.seats as seats_mod

    monkeypatch.setattr(seats_mod, "mint_seat", fake_mint)
    row = _h_invite_seat(Book(), {"desk": "bot1"}, "the-mill", "DESK_admin")
    assert row["ok"] is True
    assert seen["project"] == "ops"  # desk membership, not connect the-mill


def test_h_invite_seat_refuses_without_project(monkeypatch) -> None:
    from agent_coord.helpers.errors import CoordError
    from agent_coord.server.api.mill.rpc import _h_invite_seat

    class Book:
        _cn = object()

    monkeypatch.setattr(
        "agent_coord.server.admin.guard.require_invite_seat_mint", lambda *a, **k: None
    )
    monkeypatch.setattr(
        "agent_coord.server.api.mill.rpc._seat_roster", lambda cn, desk: "Office"
    )
    with pytest.raises(CoordError, match="invite-seat: roster required"):
        _h_invite_seat(Book(), {"desk": "new-bot"}, "the-mill", "DESK_admin")


def test_cli_invite_seat_omits_project_when_unset(monkeypatch, capsys) -> None:
    from agent_coord.__main__ import _invite_cmd

    seen: dict = {}

    def call(body):
        seen.update(body)
        return {
            "ok": True,
            "desk": "bot3",
            "seat": "S3",
            "invite_url": "https://203.0.113.10/welcome?desk=bot3&seat=S3&project=ops",
            "status": "ready",
            "project": "ops",
        }

    monkeypatch.setattr("agent_coord.client.http.mill_http_call", call)
    monkeypatch.setattr(
        "agent_coord.client.tokens.resolve_desk_owner",
        lambda _ignored="": "DESK_admin",
    )
    monkeypatch.setattr(
        "agent_coord.client.http.mill_url",
        lambda: "https://203.0.113.10",
    )
    args = SimpleNamespace(
        owner="DESK_admin",
        door="",
        rotate=False,
        mint=False,
        enable="",
        invite_list=False,
        revoke="",
        ttl="",
        ttl_for="",
        label="",
        seat="bot3",
        join="",
        party="human",
        party_id="",
        lan_only=None,
        cmd="invite",
        project="",  # no --project
    )
    rc = _invite_cmd(args)
    assert rc == 0
    assert seen["verb"] == "invite-seat"
    assert "project" not in seen
