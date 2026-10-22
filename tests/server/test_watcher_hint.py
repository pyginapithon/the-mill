"""watcher.hint - per-listener detail on fanout."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from agent_coord.server import push


def test_cheap_detail_shape_no_body():
    cn = MagicMock()
    cur = MagicMock()
    cn.cursor.return_value = cur
    cur.fetchall.return_value = [{"name_id": 58, "lft": 1, "rgt": 10}]
    with patch("agent_coord.server.records.activity.get", return_value=
        {"type": "mail", "id": 42, "updated": "2026-09-19T12:00:00"}
    ):
        raw = push._cheap_detail(cn, "mail", 42, [{"desk": "DESK_a"}, {"desk": "DESK_b"}])
    d = json.loads(raw)
    assert d["what"] == "mail"
    assert d["id"] == 42
    assert d["watchers"] == 2
    assert d["when"]
    assert "body" not in d
    assert "state" in d and d["state"] is None
    assert len(raw) <= 4096


def test_cheap_detail_carries_state():
    """#93: soft-deleted activity shows on the doorbell detail."""
    cn = MagicMock()
    cur = MagicMock()
    cn.cursor.return_value = cur
    cur.fetchall.return_value = []
    rows = {
        ("todo", 5): {"type": "todo", "id": 5, "updated": "2026-10-08T12:00:00", "state": "deleted"},
        ("mail", 6): {"type": "mail", "id": 6, "updated": "2026-10-08T12:00:00", "state": "sent"},
    }
    with patch("agent_coord.server.records.activity.get", side_effect=lambda _cn, t, i: rows.get((t, i))):
        gone = json.loads(push._cheap_detail(cn, "todo", 5, []))
        sent = json.loads(push._cheap_detail(cn, "mail", 6, []))
        miss = json.loads(push._cheap_detail(cn, "todo", 99, []))
    assert gone["state"] == "deleted"
    assert sent["state"] == "sent"
    assert miss["state"] is None


def test_fanout_uses_watcher_hint_per_desk():
    cn = MagicMock()
    rows = [
        {"desk": "DESK_a", "hint": "need:src,body", "delivery_mode": "polling", "endpoint_url": ""},
        {"desk": "DESK_b", "hint": None, "delivery_mode": "polling", "endpoint_url": ""},
    ]
    notified = []

    def capture(desk, payload):
        notified.append((desk, dict(payload)))

    with patch("agent_coord.server.records.watcher.select", return_value=rows), patch.object(
        push, "_cheap_detail", return_value='{"what":"mail","id":7,"watchers":2}'
    ), patch.object(push, "_desk_room_keys", side_effect=lambda d: [d]), patch.object(
        push.HUB, "rooms", {"DESK_a": {object()}, "DESK_b": {object()}}
    ), patch.object(push.HUB, "notify", side_effect=capture):
        push.fanout(cn, "mail", 7, "MAIL")

    by = {d: p for d, p in notified}
    assert by["DESK_a"]["hint"] == "MAIL"
    assert by["DESK_a"]["detail"] == "need:src,body"
    assert by["DESK_b"]["hint"] == "MAIL"
    assert by["DESK_b"]["detail"].startswith("{")
    assert "what" in by["DESK_b"]["detail"]


def test_outbound_add_remove_in_wall():
    """#265: mill add|remove replace mill watcher."""
    from agent_coord.client.outbound import WALL, COMMANDS, body_from_args

    assert "watcher" not in WALL and "watcher" not in COMMANDS
    assert {"add", "remove"} <= set(WALL) and {"add", "remove"} <= set(COMMANDS)

    class A:
        cmd = "add"
        target = ("todo", 9)
        who = ""
        hint = "src,body"
        owner = "builder"
        project = "agent-coord"

    body = body_from_args(A())
    assert body["verb"] == "add"
    assert (body["type"], body["id"]) == ("todo", 9)
    assert body["hint"] == "src,body"
    assert "who" not in body and "target" not in body
