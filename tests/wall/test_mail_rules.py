"""Table-driven mail pure rules (LIST dst filter, desk-only, autoselect).

Contract: agent_coord.web.wall_logic.mail is SoR; board.html must call-equivalent.
"""
from __future__ import annotations

import pytest

from agent_coord.web.wall_logic import (
    BOARD_EQUIVALENT_MARKER,
    mail_active_rows,
    mail_at,
    mail_attention_dsts,
    mail_desk_matches,
    mail_dst,
    mail_dst_agent_read,
    mail_dst_desks,
    mail_dst_human_opened,
    mail_is_bare_human_mailbox,
    mail_is_lean,
    mail_list_autoselect_dst,
    mail_msg_agent_unread,
    mail_msg_human_required_open,
    mail_msg_needs_attention,
    mail_resolve_list_dst,
    mail_room_cast,
    mail_lean_tos_len,
    mail_cast_count,
    mail_cast_tip,
    mail_rows_for_dst_src,
    mail_rows_for_list_dst,
    mail_sender_desk,
    mail_srcs_for_dst,
    mail_tos,
    mail_tree_root,
    mail_rooms_from_trees,
    mail_room_latest_at,
    mail_rooms_sorted_by_latest,
    mail_tree_depth0,
)
from agent_coord.web.wall_logic.mail import mail_rows_all_recent


@pytest.mark.parametrize(
    "dst,expect",
    [
        ("setter-upper", True),
        ("human", True),
        ("dead-letter", True),
        ("", True),
        ("builder", False),
        ("desk.setter-upper", False),
        ("desk.dead-letter", False),
        ("desk.builder", False),
        ("validator", False),
        ("*", False),
        ("product.mill", False),
    ],
)
def test_bare_human_mailbox(dst, expect):
    assert mail_is_bare_human_mailbox(dst) is expect


def test_active_rows_strips_bare_human():
    rows = [
        {"id": 1, "dst": "builder", "body": "a"},
        {"id": 2, "dst": "setter-upper", "body": "b"},
        {"id": 3, "dst": "human", "body": "c"},
        {"id": 4, "dst": "validator", "body": "d"},
        {"id": 5, "dst": "dead-letter", "body": "e"},
    ]
    out = mail_active_rows(rows)
    assert [m["id"] for m in out] == [1, 4]


@pytest.mark.parametrize(
    "m_dst,want,expect",
    [
        ("builder", "builder", True),
        ("desk.builder", "builder", False),
        ("builder", "validator", False),
        ("*", "*", True),
        ("product.mill", "product.mill", True),
        ("builder", "", False),
        ("desk.validator", "validator", False),
    ],
)
def test_desk_matches(m_dst, want, expect):
    assert mail_desk_matches({"dst": m_dst}, want) is expect


def test_list_filter_by_selected_dst():
    rows = [
        {"id": 1, "dst": "builder", "at": "2026-09-10T12:00:00", "read_agent": False},
        {"id": 2, "dst": "validator", "at": "2026-09-10T13:00:00", "read_agent": False},
        {"id": 3, "dst": "builder", "at": "2026-09-10T14:00:00", "read_agent": False},
        {"id": 4, "dst": "desk.builder", "at": "2026-09-10T11:00:00", "read_agent": False},
    ]
    assert mail_rows_for_list_dst(rows, "", "all") == []
    only_b = mail_rows_for_list_dst(rows, "builder", "all")
    assert [m["id"] for m in only_b] == [3, 1]
    only_v = mail_rows_for_list_dst(rows, "validator", "all")
    assert [m["id"] for m in only_v] == [2]


def test_list_attention_mode_filters():
    rows = [
        {"id": 1, "dst": "builder", "at": "2026-09-10T12:00:00", "read_agent": True},
        {"id": 2, "dst": "builder", "at": "2026-09-10T13:00:00", "read_agent": False},
        {
            "id": 3,
            "dst": "builder",
            "at": "2026-09-10T14:00:00",
            "read_agent": True,
            "human_required": True,
        },
    ]
    out = mail_rows_for_list_dst(rows, "builder", "attention")
    assert [m["id"] for m in out] == [3, 2]


def test_list_recent_mode_caps_80():
    rows = [
        {"id": i, "dst": "builder", "at": f"2026-09-10T{i:02d}:00:00", "read_agent": True}
        for i in range(100)
    ]
    out = mail_rows_for_list_dst(rows, "builder", "recent")
    assert len(out) == 80
    assert out[0]["id"] == 99


@pytest.mark.parametrize(
    "m,expect",
    [
        ({"dst": "builder", "read_agent": False}, True),
        ({"dst": "builder", "read_agent": True}, False),
        ({"dst": "*", "read_agent": False}, False),
        ({"dst": "builder", "read_agent": True, "human_required": True}, True),
        (
            {
                "dst": "builder",
                "read_agent": True,
                "human_required": True,
                "human_acked": True,
            },
            False,
        ),
        (
            {
                "dst": "builder",
                "read_agent": True,
                "human_required": True,
                "human_required_status": "cleared",
            },
            False,
        ),
        (
            {
                "dst": "builder",
                "read_agent": True,
                "needs_human": True,
            },
            True,
        ),
    ],
)
def test_needs_attention(m, expect):
    assert mail_msg_needs_attention(m) is expect


def test_agent_read_via_reads_and_readers():
    m_reads = {
        "dst": "builder",
        "reads": [{"desk": "builder", "party": "agent", "who": "builder"}],
    }
    assert mail_dst_agent_read(m_reads) is True
    assert mail_msg_needs_attention(m_reads) is False
    m_readers = {"dst": "builder", "readers": ["builder:agent:sess"]}
    assert mail_dst_agent_read(m_readers) is True
    m_human_only = {
        "dst": "builder",
        "reads": [{"desk": "builder", "party": "human", "who": "setter-upper"}],
    }
    assert mail_dst_agent_read(m_human_only) is False
    assert mail_dst_human_opened(m_human_only) is True


def test_human_opened_readers_legacy():
    m = {"dst": "builder", "readers": ["builder:human"]}
    assert mail_dst_human_opened(m) is True
    assert mail_dst_agent_read(m) is False


def test_autoselect_prefers_needs_then_first():
    dsts = [
        {"id": "coord", "needsAttention": False},
        {"id": "builder", "needsAttention": True},
        {"id": "validator", "needsAttention": False},
    ]
    assert mail_list_autoselect_dst(dsts, mode="attention", selected="") == "builder"
    assert mail_list_autoselect_dst(dsts, mode="all", selected="") == "coord"
    assert mail_list_autoselect_dst(dsts, mode="attention", selected="validator") == "builder"
    assert mail_list_autoselect_dst(dsts, mode="attention", selected="builder") == "builder"
    assert mail_list_autoselect_dst(dsts, mode="attention", selected="", view="graph") == ""
    assert mail_list_autoselect_dst(dsts, mode="all", selected="validator") == "validator"


def test_attention_snap_when_selected_not_needs():
    """Board mail(): attention mode snaps off non-Needs selected dst."""
    dsts = [
        {"id": "coord", "needsAttention": False},
        {"id": "builder", "needsAttention": True},
    ]
    assert mail_resolve_list_dst(dsts, mode="attention", selected="coord") == "builder"
    assert mail_attention_dsts(dsts)[0]["id"] == "builder"


def test_graph_view_no_list_autoselect():
    dsts = [{"id": "builder", "needsAttention": True}]
    assert mail_list_autoselect_dst(dsts, mode="attention", selected="", view="graph") == ""
    assert (
        mail_list_autoselect_dst(dsts, mode="attention", selected="validator", view="graph")
        == "validator"
    )


def test_dst_src_filter_graph_col3():
    rows = [
        {"id": 1, "dst": "builder", "src": "auditor", "at": "2026-09-10T12:00:00", "read_agent": False},
        {"id": 2, "dst": "builder", "src": "validator", "at": "2026-09-10T13:00:00", "read_agent": True},
        {"id": 3, "dst": "builder", "src": "auditor", "at": "2026-09-10T14:00:00", "read_agent": True, "human_required": True},
        {"id": 4, "dst": "validator", "src": "auditor", "at": "2026-09-10T15:00:00", "read_agent": False},
    ]
    assert mail_rows_for_dst_src(rows, "", "auditor", "all") == []
    only = mail_rows_for_dst_src(rows, "builder", "auditor", "all")
    # unread/HR first: id1 unread, id3 HR, then by at
    assert [m["id"] for m in only] == [1, 3]
    srcs = mail_srcs_for_dst(rows, "builder")
    assert [s["id"] for s in srcs] == ["auditor", "validator"]
    assert srcs[0]["agentUnread"] == 1
    assert srcs[0]["humanRequired"] == 1


def test_rows_all_recent_attention_excludes_floor():
    rows = [
        {"id": 1, "dst": "*", "at": "2026-09-10T15:00:00", "read_agent": False},
        {"id": 2, "dst": "builder", "at": "2026-09-10T14:00:00", "read_agent": False},
    ]
    out = mail_rows_all_recent(rows, "attention")
    assert [m["id"] for m in out] == [2]


def test_board_equivalent_marker_stable():
    assert BOARD_EQUIVALENT_MARKER == "WALL_LOGIC_MAIL_SOR"


def _lean(sender="a", tos=None, body="hi", created="2026-09-26T12:00:00", **extra_fields):
    row = {
        "id": extra_fields.pop("id", 1),
        "created": created,
        "sender": {"deskId": sender, "roster": None},
        "body": body,
        "mail_tos": tos if tos is not None else [{"deskId": "b", "roster": None, "receipt": 0}],
    }
    row.update(extra_fields)
    return row


def test_lean_adapters_sender_tos_cast_dst():
    m = _lean(
        tos=[
            {"deskId": "b", "roster": None, "receipt": 0},
            {"deskId": "c", "roster": "builder", "receipt": 1},
        ]
    )
    assert mail_is_lean(m) is True
    assert mail_sender_desk(m) == "a"
    assert mail_dst(m) == "b"
    assert mail_dst_desks(m) == ["b", "c"]
    assert mail_at(m) == "2026-09-26T12:00:00"
    assert [t["deskId"] for t in mail_tos(m)] == ["b", "c"]
    cast = mail_room_cast(m)
    assert [c["deskId"] for c in cast] == ["a", "b", "c"]
    assert mail_desk_matches(m, "c") is True
    assert mail_desk_matches(m, "a") is False  # sender is cast, not dest
    assert mail_desk_matches(m, "z") is False


def test_lean_cast_count_and_tip():
    m = _lean(
        tos=[
            {"deskId": "b", "roster": None, "receipt": 0},
            {"deskId": "c", "roster": "builder", "receipt": 1},
        ]
    )
    assert mail_lean_tos_len(m) == 2
    assert mail_cast_count(m) == 3  # 1 sender + len(mail_tos)
    tip = mail_cast_tip(m)
    assert tip.startswith("from a")
    assert "to b" in tip
    assert "to c (builder)" in tip
    legacy = {"id": 9, "src": "a", "dst": "b", "body": "x"}
    assert mail_cast_count(legacy) == 0
    assert mail_lean_tos_len(legacy) == 0


def test_lean_receipt_is_human_required_not_opened():
    quiet = _lean(tos=[{"deskId": "b", "roster": None, "receipt": 0}])
    hot = _lean(tos=[{"deskId": "b", "roster": None, "receipt": 1}])
    assert mail_msg_human_required_open(quiet) is False
    assert mail_msg_human_required_open(hot) is True
    # Lean cast has no opened/reads: do not invent agent-unread.
    assert mail_msg_agent_unread(quiet) is False
    assert mail_msg_agent_unread(hot) is False
    assert mail_msg_needs_attention(hot) is True
    assert mail_msg_needs_attention(quiet) is False
    assert "opened" not in quiet and "opened" not in hot


def test_lean_list_filter_and_srcs():
    rows = [
        _lean(id=1, sender="auditor", tos=[{"deskId": "builder", "roster": None, "receipt": 0}], created="2026-09-10T12:00:00"),
        _lean(id=2, sender="validator", tos=[{"deskId": "builder", "roster": None, "receipt": 1}], created="2026-09-10T13:00:00"),
        _lean(id=3, sender="auditor", tos=[{"deskId": "validator", "roster": None, "receipt": 0}], created="2026-09-10T14:00:00"),
    ]
    only = mail_rows_for_list_dst(rows, "builder", "all")
    assert [m["id"] for m in only] == [2, 1]
    attn = mail_rows_for_list_dst(rows, "builder", "attention")
    assert [m["id"] for m in attn] == [2]
    srcs = mail_srcs_for_dst(rows, "builder")
    assert [s["id"] for s in srcs] == ["validator", "auditor"]
    assert srcs[0]["humanRequired"] == 1


def test_desk_matches_stored_name():
    """A destination matches the stored name. A prefixed token is a different string."""
    m = _lean(sender="auditor", tos=[{"deskId": "builder", "roster": None, "receipt": 0}])
    assert mail_desk_matches(m, "builder") is True
    assert mail_desk_matches(m, "PROJ_the-mill:builder") is False
    assert mail_desk_matches(m, {"type": "desk", "name": "builder"}) is True
    assert mail_desk_matches(m, {"type": "roster", "name": "builder"}) is True
    named = {"dst": {"type": "desk", "name": "builder"}}
    assert mail_desk_matches(named, {"type": "desk", "name": "builder"}) is True
    assert mail_desk_matches(named, {"type": "roster", "name": "builder"}) is False
    assert mail_desk_matches({"dst": "PROJ_the-mill:builder"}, "builder") is False


def test_srcs_for_dst_name_and_star():
    """Srcs follow the stored destination name. Star still yields srcs."""
    rows = [
        _lean(id=1, sender="auditor", tos=[{"deskId": "builder", "roster": None, "receipt": 0}], created="2026-09-10T12:00:00"),
        _lean(id=2, sender="validator", tos=[{"deskId": "builder", "roster": None, "receipt": 0}], created="2026-09-10T13:00:00"),
        {"id": 3, "dst": "*", "src": "coord", "at": "2026-09-10T14:00:00", "read_agent": False},
    ]
    srcs = mail_srcs_for_dst(rows, "builder")
    assert [s["id"] for s in srcs] == ["auditor", "validator"]
    assert mail_srcs_for_dst(rows, "PROJ_the-mill:builder") == []
    star = mail_srcs_for_dst(rows, "*")
    assert [s["id"] for s in star] == ["coord"]
    # true floor (no dest) still skipped for non-star
    floor_rows = [
        _lean(id=9, sender="ghost", tos=[], created="2026-09-10T15:00:00"),
        _lean(id=10, sender="auditor", tos=[{"deskId": "builder", "roster": None, "receipt": 0}], created="2026-09-10T16:00:00"),
    ]
    assert [s["id"] for s in mail_srcs_for_dst(floor_rows, "builder")] == ["auditor"]


def test_mail_tree_root_mail_lft1_per_name_id():
    """MAIL room root = WHERE type='mail' AND lft=1 (Rooms root SELECT; no GROUP BY)."""
    nodes = [
        {"type": "mail", "id": 101, "lft": 1, "rgt": 8, "depth": 0, "title": "thread root"},
        {"type": "mail", "id": 102, "lft": 2, "rgt": 3, "depth": 1, "title": "reply"},
        {"type": "mail", "id": 103, "lft": 4, "rgt": 5, "depth": 1, "title": "done"},
        {"type": "todo", "id": 9, "lft": 6, "rgt": 7, "depth": 1, "title": "side"},
    ]
    root = mail_tree_root(nodes)
    assert root is not None
    assert root["type"] == "mail"
    assert root["id"] == 101
    assert int(root["lft"]) == 1
    assert mail_tree_root([]) is None
    assert mail_tree_root(None) is None


def test_mail_tree_root_rejects_non_mail_lft1():
    """name/todo @ lft=1 is not a MAIL room; exclude that name_id from Rooms list."""
    nodes = [
        {"type": "name", "id": 7, "lft": 1, "rgt": 8, "depth": 0, "title": "stand-up"},
        {"type": "mail", "id": 101, "lft": 2, "rgt": 3, "depth": 1, "title": "first mail"},
        {"type": "mail", "id": 102, "lft": 4, "rgt": 5, "depth": 1, "title": "reply"},
    ]
    assert mail_tree_root(nodes) is None


def test_mail_rooms_from_trees_type_mail_lft1():
    """Room list = floor.trees whose root matches WHERE type='mail' AND lft=1 (no GROUP BY)."""
    trees = [
        {
            "name": "TREE_mail_ok",
            "nodes": [
                {"type": "mail", "id": 1, "lft": 1, "rgt": 4},
                {"type": "mail", "id": 2, "lft": 2, "rgt": 3},
            ],
        },
        {
            "name": "TREE_name_root",
            "nodes": [
                {"type": "name", "id": 9, "lft": 1, "rgt": 4},
                {"type": "mail", "id": 3, "lft": 2, "rgt": 3},
            ],
        },
        {
            "name": "TREE_mail_other",
            "nodes": [
                {"type": "mail", "id": 10, "lft": 1, "rgt": 2},
            ],
        },
        {"name": "TREE_empty", "nodes": []},
    ]
    rooms = mail_rooms_from_trees(trees)
    assert [r["name"] for r in rooms] == ["TREE_mail_ok", "TREE_mail_other"]
    assert mail_tree_root(rooms[0]["nodes"])["id"] == 1
    assert mail_tree_root(rooms[1]["nodes"])["id"] == 10


def test_mail_tree_depth0_crumbs_inside_name_id():
    """Depth-0 helper is crumbs-only inside one name_id; not Rooms list."""
    nodes = [
        {"type": "name", "id": 7, "lft": 1, "rgt": 8, "depth": 0, "title": "stand-up"},
        {"type": "mail", "id": 101, "lft": 2, "rgt": 3, "depth": 1, "title": "first mail"},
    ]
    d0 = mail_tree_depth0(nodes)
    assert d0["type"] == "name"
    assert d0["id"] == 7
    # Rooms list still rejects (root is not type=mail AND lft=1)
    assert mail_tree_root(nodes) is None


def test_mail_room_latest_at_and_rooms_sorted_by_latest():
    """Rooms left pane: most recent first; clock = lean created / legacy at (mail_at)."""
    trees = [
        {
            "name": "TREE_old",
            "nodes": [
                {"type": "mail", "id": 1, "lft": 1, "rgt": 4},
                {"type": "mail", "id": 2, "lft": 2, "rgt": 3},
            ],
        },
        {
            "name": "TREE_new",
            "nodes": [
                {"type": "mail", "id": 10, "lft": 1, "rgt": 4},
                {"type": "mail", "id": 11, "lft": 2, "rgt": 3},
            ],
        },
        {
            "name": "TREE_name_root",
            "nodes": [
                {"type": "name", "id": 9, "lft": 1, "rgt": 4},
                {"type": "mail", "id": 3, "lft": 2, "rgt": 3},
            ],
        },
    ]
    mailbox = [
        {"id": 1, "created": "2026-09-20 10:00:00", "sender": {"deskId": "a"}, "mail_tos": []},
        {"id": 2, "created": "2026-09-21 12:00:00", "sender": {"deskId": "a"}, "mail_tos": []},
        {"id": 10, "created": "2026-09-22 08:00:00", "sender": {"deskId": "b"}, "mail_tos": []},
        {"id": 11, "at": "2026-09-25 15:00:00", "src": "b", "dst": "c"},  # legacy at wins vs older sibling
        {"id": 3, "created": "2026-09-26 99:00:00", "sender": {"deskId": "z"}, "mail_tos": []},
    ]
    assert mail_room_latest_at(trees[0], mailbox) == "2026-09-21 12:00:00"
    assert mail_room_latest_at(trees[1], mailbox) == "2026-09-25 15:00:00"
    # name_id with non-mail root is not a Rooms forest; helper still maxes mail under nodes
    assert mail_room_latest_at(trees[2], mailbox) == "2026-09-26 99:00:00"
    sorted_rooms = mail_rooms_sorted_by_latest(trees, mailbox)
    assert [r["name"] for r in sorted_rooms] == ["TREE_new", "TREE_old"]
    assert mail_room_latest_at(None, mailbox) == ""
    assert mail_room_latest_at(trees[0], None) == ""
