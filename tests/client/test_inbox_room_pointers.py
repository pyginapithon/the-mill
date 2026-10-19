"""Inbox names a mail-thread catch-up per room it saw (#79)."""
from __future__ import annotations

import json
from types import SimpleNamespace

import agent_coord.client.http as h


def _letter(mid, tree="", root=0):
    row = {"id": mid, "body": "x", "mail_tos": []}
    if tree:
        row["tree"] = tree
        row["root_id"] = root
        row["root_type"] = "mail"
    return row


def test_pointers_one_per_room_sorted_with_counts():
    rows = [
        _letter(300, "build-room", 191),
        _letter(301),
        _letter(302, "TREE_ab12", 74),
        _letter(303, "build-room", 191),
    ]
    got = h.inbox_room_pointers(rows)
    assert got == [
        {"tree": "TREE_ab12", "root_id": 74, "letters": 1, "catch_up": "mill mail-thread 302"},
        {"tree": "build-room", "root_id": 191, "letters": 2, "catch_up": "mill mail-thread 303"},
    ]


def test_pointers_skip_off_tree_and_bad_rows():
    rows = [_letter(1), {"id": 2, "tree": "t", "root_id": "nope"}, "junk", {"id": 3, "root_id": 9}]
    assert h.inbox_room_pointers(rows) == []
    assert h.inbox_room_pointers(None) == []
    assert h.inbox_room_pointers({"id": 1}) == []


def _run(monkeypatch, capsys, cmd, reply, raw=False):
    monkeypatch.setattr(h, "mill_http_call", lambda body: reply)
    monkeypatch.setattr(
        "agent_coord.client.outbound.body_from_args", lambda args: {"verb": cmd}
    )
    rc = h.mill_http_from_args(SimpleNamespace(cmd=cmd, raw=raw))
    return rc, capsys.readouterr().out


def test_inbox_envelope_gets_rooms(monkeypatch, capsys):
    reply = {
        "id": "r1",
        "ok": True,
        "mill": "0.0.0",
        "result": [_letter(300, "build-room", 191), _letter(301)],
        "sync": [],
    }
    rc, out = _run(monkeypatch, capsys, "inbox", reply)
    assert rc == 0
    obj = json.loads(out)
    # 0.7.x: inbox groups by room tree by default; letters off a room sit under (none).
    assert obj["result"]["group_by"] == "tree"
    assert [[r["id"] for r in g["items"]] for g in obj["result"]["groups"]] == [[300], [301]]
    assert obj["sync"] == []
    assert obj["rooms"] == [
        {"tree": "build-room", "root_id": 191, "letters": 1, "catch_up": "mill mail-thread 300"}
    ]
    assert "rooms" not in reply  # caller reply not mutated
    out.encode("ascii")


def test_inbox_no_rooms_key_when_no_tree_letters(monkeypatch, capsys):
    reply = {"id": "r2", "ok": True, "mill": "0", "result": [_letter(5)], "sync": []}
    _, out = _run(monkeypatch, capsys, "inbox", reply)
    assert "rooms" not in json.loads(out)


def test_empty_page_keeps_stashed_rooms(monkeypatch, capsys, tmp_path):
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    monkeypatch.setattr(
        "agent_coord.client.outbound.body_from_args",
        lambda args: {"verb": "inbox", "owner": "cold-ab-s"},
    )
    first = {
        "id": "r4",
        "ok": True,
        "mill": "0",
        "result": [
            _letter(300, "build-room", 191),
            _letter(301, "build-room", 191),
            _letter(302, "agent-ux", 57),
        ],
        "sync": [],
    }
    monkeypatch.setattr(h, "mill_http_call", lambda body: first)
    rc = h.mill_http_from_args(SimpleNamespace(cmd="inbox", raw=False))
    assert rc == 0
    capsys.readouterr()
    # This page sees build-room once. agent-ux is absent and must stay.
    second = {
        "id": "r5",
        "ok": True,
        "mill": "0",
        "result": [_letter(400, "build-room", 191)],
        "sync": [],
    }
    monkeypatch.setattr(h, "mill_http_call", lambda body: second)
    rc = h.mill_http_from_args(SimpleNamespace(cmd="inbox", raw=False))
    assert rc == 0
    page = json.loads(capsys.readouterr().out)
    assert page["rooms"] == [
        {"tree": "agent-ux", "root_id": 57, "letters": 1, "catch_up": "mill mail-thread 302"},
        {"tree": "build-room", "root_id": 191, "letters": 1, "catch_up": "mill mail-thread 400"},
    ]
    empty = {"id": "r6", "ok": True, "mill": "0", "result": [], "sync": []}
    monkeypatch.setattr(h, "mill_http_call", lambda body: empty)
    rc = h.mill_http_from_args(SimpleNamespace(cmd="inbox", raw=False))
    assert rc == 0
    obj = json.loads(capsys.readouterr().out)
    assert obj["result"] == []
    assert obj["rooms"] == page["rooms"]
    assert (tmp_path / "inbox-rooms" / "cold-ab-s.json").is_file()


def test_empty_desk_does_not_write_room_stash(monkeypatch, capsys, tmp_path):
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    reply = {
        "id": "r7",
        "ok": True,
        "mill": "0",
        "result": [_letter(300, "build-room", 191)],
        "sync": [],
    }
    _, out = _run(monkeypatch, capsys, "inbox", reply)
    assert "rooms" in json.loads(out)
    assert not (tmp_path / "inbox-rooms").exists()


def test_raw_and_other_verbs_unchanged(monkeypatch, capsys):
    rows = [_letter(300, "build-room", 191)]
    reply = {"id": "r3", "ok": True, "mill": "0", "result": rows, "sync": []}
    _, out = _run(monkeypatch, capsys, "inbox", reply, raw=True)
    assert json.loads(out) == rows
    _, out = _run(monkeypatch, capsys, "mail-thread", reply)
    assert "rooms" not in json.loads(out)
