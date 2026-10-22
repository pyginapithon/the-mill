# -*- coding: utf-8 -*-
"""Security: the Admin gate on member-add/remove holds for every spelling (#675).

The name table is case- and accent-insensitive, so "admin" names the same
roster row as "Admin". The handler gates on the resolved roster, not the raw
string, and mill_member_put / mill_member_delete refuse the Admin roster
outright; only the office host path (mill_member_admin_put/delete) moves a
desk on or off Admin.
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import mysql.connector
import pytest

from agent_coord.helpers.errors import CoordError
from agent_coord.server.admin.guard import ADMIN_ROSTER_ID, is_role_admin
from agent_coord.server.api.mill import rpc
from agent_coord.server.records import member as rec_member
from tests.server.records.conftest import seed_names

pytestmark = pytest.mark.sql

SPELLINGS = ("admin", "ADMIN", " Admin ", "aDmIn", "\u00c1dmin", "adm\u00edn")


def _member(cn, command, group, owner, desk="", host=False):
    body = {"verb": command, "group": group}
    if desk:
        body["desk"] = desk
    if host:
        body["host"] = True
    with patch.object(rpc, "_h_send", return_value={"id": 1}):
        return rpc._h_member(SimpleNamespace(_cn=cn), body, "Office", owner)


@pytest.fixture(scope="module")
def desks(cn):
    seed_names(cn, ("m675-plain", "desk"), ("m675-admin", "desk"), ("m675-other", "desk"),
               ("m675-room", "roster"))
    rec_member.put_office(cn, "m675-plain")
    rec_member.put_office(cn, "m675-admin")
    cur = cn.cursor()
    try:  # seed straight in SQL, so the fixture does not lean on the code under test
        cur.execute(
            "INSERT IGNORE INTO member (name_id, desk_id)"
            " SELECT %s, id FROM name WHERE type = 'desk' AND name = 'm675-admin'",
            (ADMIN_ROSTER_ID,),
        )
        cn.commit()
    finally:
        cur.close()
    assert is_role_admin(cn, "m675-admin") is True
    return True


@pytest.mark.parametrize("spelling", SPELLINGS)
def test_off_host_member_add_admin_any_spelling_refused(cn, desks, spelling):
    with pytest.raises(CoordError) as ei:
        _member(cn, "member-add", spelling, "m675-plain")
    assert "office host only" in str(ei.value)
    assert is_role_admin(cn, "m675-plain") is False


@pytest.mark.parametrize("spelling", SPELLINGS)
def test_off_host_member_add_other_desk_to_admin_refused(cn, desks, spelling):
    with pytest.raises(CoordError):
        _member(cn, "member-add", spelling, "m675-plain", desk="m675-other")
    assert is_role_admin(cn, "m675-other") is False


@pytest.mark.parametrize("spelling", SPELLINGS)
def test_off_host_member_remove_admin_any_spelling_refused(cn, desks, spelling):
    with pytest.raises(CoordError) as ei:
        _member(cn, "member-remove", spelling, "m675-plain", desk="m675-admin")
    assert "office host only" in str(ei.value)
    assert is_role_admin(cn, "m675-admin") is True


@pytest.mark.parametrize("spelling", ("Admin", "admin", "\u00c1dmin"))
def test_sql_member_put_refuses_admin_roster(cn, desks, spelling):
    """SQL is authoritative: the generic put never reaches the Admin roster."""
    with pytest.raises(mysql.connector.Error) as ei:
        rec_member.put(cn, spelling, "m675-plain", "roster")
    assert "office host only" in str(ei.value)
    assert is_role_admin(cn, "m675-plain") is False


@pytest.mark.parametrize("spelling", ("Admin", "admin", "\u00c1dmin"))
def test_sql_member_delete_refuses_admin_roster(cn, desks, spelling):
    with pytest.raises(mysql.connector.Error) as ei:
        rec_member.delete(cn, spelling, "m675-admin", "roster")
    assert "office host only" in str(ei.value)
    assert is_role_admin(cn, "m675-admin") is True


def test_host_member_add_and_remove_admin_still_work(cn, desks):
    rows = _member(cn, "member-add", "admin", "m675-admin", desk="m675-other", host=True)
    assert rows and int(rows[0]["name_id"]) == ADMIN_ROSTER_ID
    assert rows[0]["roster"] == "Admin"
    assert is_role_admin(cn, "m675-other") is True
    _member(cn, "member-remove", "ADMIN", "m675-admin", desk="m675-other", host=True)
    assert is_role_admin(cn, "m675-other") is False


def test_host_member_remove_admin_needs_admin_caller(cn, desks):
    with pytest.raises(CoordError) as ei:
        _member(cn, "member-remove", "admin", "m675-plain", desk="m675-admin", host=True)
    assert "mill Admin required" in str(ei.value)
    assert is_role_admin(cn, "m675-admin") is True


def test_other_rosters_unchanged(cn, desks):
    rows = _member(cn, "member-add", "m675-room", "m675-plain")
    assert rows and rows[0]["op"] == "added"
    _member(cn, "member-remove", "m675-room", "m675-plain")
    assert is_role_admin(cn, "m675-plain") is False
