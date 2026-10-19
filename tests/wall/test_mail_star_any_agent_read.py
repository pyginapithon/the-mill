# -*- coding: utf-8 -*-
"""PLAN #32: Wall * looks read if any agent marked; desk unread stays per-desk."""
from __future__ import annotations

from agent_coord.web.wall_logic.mail import (
    mail_msg_agent_unread,
    mail_msg_needs_attention,
    mail_star_any_agent_read,
    mail_star_wall_unread,
    mail_wall_unread,
)


def test_star_unread_until_any_agent_marks():
    raw = {"dst": "*", "reads": []}
    assert mail_star_any_agent_read(raw) is False
    assert mail_star_wall_unread(raw) is True
    assert mail_wall_unread(raw) is True
    assert mail_msg_agent_unread(raw) is False
    assert mail_msg_needs_attention(raw) is False


def test_star_read_if_any_agent_desk_marked():
    marked = {
        "dst": "*",
        "reads": [
            {"desk": "builder", "party": "agent", "who": "builder:agent:grok"},
        ],
    }
    assert mail_star_any_agent_read(marked) is True
    assert mail_star_wall_unread(marked) is False
    assert mail_wall_unread(marked) is False
    assert mail_msg_agent_unread(marked) is False


def test_star_flag_read_star_any_agent():
    m = {"dst": "*", "read_star_any_agent": True, "reads": []}
    assert mail_star_any_agent_read(m) is True
    assert mail_wall_unread(m) is False


def test_desk_unread_unchanged_by_star_helpers():
    desk = {"dst": "validator", "read_agent": False, "reads": []}
    other_marked = {
        "dst": "validator",
        "reads": [{"desk": "builder", "party": "agent"}],
    }
    assert mail_wall_unread(desk) is True
    assert mail_msg_agent_unread(desk) is True
    assert mail_star_any_agent_read(desk) is False
    assert mail_star_wall_unread(other_marked) is False
    assert mail_wall_unread(other_marked) is True
    assert mail_msg_agent_unread(other_marked) is True
