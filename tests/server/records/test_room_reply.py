# -*- coding: utf-8 -*-
"""Room backend: send --room opens Host TREE; multi-To alone plain; reply nests / opens room."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.sql

from agent_coord.server.records import mail as rec_mail
from agent_coord.server.records import name as rec_name
from agent_coord.server.records import tree as rec_tree
from agent_coord.server.api.mill import rpc
from tests.server.records.conftest import seed_names


class _Book:
    def __init__(self, cn):
        self._cn = cn



def _node(book, verb: str, mid: int, who: str, owner: str) -> dict:
    """mill add|remove mail:MID WHO (#265), replacing reply --add-to/--remove-to."""
    return rpc._h_add_remove(book, {"verb": verb, "type": "mail", "id": int(mid), "who": who}, "unit", owner)


def _desks(cn, mid: int) -> set[str]:
    return {str(r.get("desk") or "") for r in rec_mail.to_list(cn, int(mid))}


def test_send_one_dest_no_tree(cn) -> None:
    seed_names(cn, ("unit", "roster"), ("a", "desk"), ("b", "desk"))
    book = _Book(cn)
    rec = rpc._h_send(
        book,
        {"project": "unit", "src": "a", "dst": "b", "body": "plain one dest"},
        "unit",
        "a",
    )
    mid = int(rec["id"])
    assert not rec_tree.on_tree(cn, "mail", mid)
    desks = {t["deskId"] for t in (rec.get("mail_tos") or [])}
    assert "b" in desks


def test_send_multi_dest_no_tree_without_name(cn) -> None:
    """Multi-To alone is plain mail (Host lock: room only with --room)."""
    seed_names(cn, ("unit", "roster"), ("a", "desk"), ("b", "desk"), ("c", "desk"))
    book = _Book(cn)
    rec = rpc._h_send(
        book,
        {"project": "unit", "src": "a", "dst": "b,c", "body": "multi plain"},
        "unit",
        "a",
    )
    mid = int(rec["id"])
    assert not rec_tree.on_tree(cn, "mail", mid)
    assert rec.get("room") is not True
    desks = {t["deskId"] for t in (rec.get("mail_tos") or [])}
    assert {"b", "c"} <= desks
    assert rec_mail.dest_count(cn, mid) == 2


def test_send_with_name_opens_host_room(cn) -> None:
    """--room stores that room name and opens the mail room."""
    seed_names(cn, ("unit", "roster"), ("a", "desk"), ("b", "desk"), ("c", "desk"))
    book = _Book(cn)
    slug = "dev-standup-2026-09-27"
    rec = rpc._h_send(
        book,
        {"project": "unit", "src": "a", "dst": "b,c", "body": "room open", "name": slug},
        "unit",
        "a",
    )
    mid = int(rec["id"])
    assert rec_tree.on_tree(cn, "mail", mid)
    assert rec.get("room") is True
    crumbs = rec_mail.tree_crumbs(cn, mid)
    assert crumbs.get("root_id") == mid
    assert crumbs.get("tree") == slug
    # mail-thread by Host slug == by root id
    by_id = rpc._h_mail_thread(book, {"mail_id": mid}, "unit", "a")
    by_host = rpc._h_mail_thread(book, {"tree": slug}, "unit", "a")
    assert [int(m["id"]) for m in by_host["chain"]] == [int(m["id"]) for m in by_id["chain"]]
    assert by_host.get("tree") == slug
    assert by_host.get("root_id") == mid


def test_send_name_conflict_coorderror(cn) -> None:
    from agent_coord.helpers.errors import CoordError

    seed_names(cn, ("unit", "roster"), ("a", "desk"), ("b", "desk"), ("c", "desk"))
    book = _Book(cn)
    slug = "standup-conflict-room"
    rpc._h_send(
        book,
        {"project": "unit", "src": "a", "dst": "b,c", "body": "first", "name": slug},
        "unit",
        "a",
    )
    with pytest.raises(CoordError) as ei:
        rpc._h_send(
            book,
            {"project": "unit", "src": "a", "dst": "b", "body": "dup", "name": slug},
            "unit",
            "a",
        )
    assert "already exists" in str(ei.value).lower() or "exists" in str(ei.value).lower()


def test_reply_nests_and_defaults_reply_all(cn) -> None:
    seed_names(cn, ("unit", "roster"), ("a", "desk"), ("b", "desk"), ("c", "desk"))
    book = _Book(cn)
    root = rpc._h_send(
        book,
        {"project": "unit", "src": "a", "dst": "b,c", "body": "root"},
        "unit",
        "a",
    )
    rid = int(root["id"])
    rep = rpc._h_reply(
        book,
        {"mail_id": rid, "body": "child reply", "src": "b"},
        "unit",
        "b",
    )
    cid = int(rep["id"])
    assert rep.get("parent_id") == rid or rep.get("replied_to") == rid
    assert rec_tree.has_parent(cn, "mail", cid)
    crumbs = rec_mail.tree_crumbs(cn, cid)
    assert crumbs.get("parent_id") == rid
    assert crumbs.get("root_id") == rid
    desks = {t["deskId"] for t in (rep.get("mail_tos") or [])}
    # reply-all: parent sender {a} U parent mail_tos {b,c}, exclude self b => {a,c}
    assert desks == {"a", "c"}
    # sender is object
    assert isinstance(rep.get("sender"), dict)
    assert rep["sender"]["deskId"] == "b"


def test_reply_opens_room_when_parent_off_tree(cn) -> None:
    seed_names(cn, ("unit", "roster"), ("a", "desk"), ("b", "desk"))
    book = _Book(cn)
    # single dest => plain mail, no TREE
    plain = rpc._h_send(
        book,
        {"project": "unit", "src": "a", "dst": "b", "body": "no room yet"},
        "unit",
        "a",
    )
    pid = int(plain["id"])
    assert not rec_tree.on_tree(cn, "mail", pid)
    rep = rpc._h_reply(
        book,
        {"mail_id": pid, "body": "first reply opens room", "src": "b"},
        "unit",
        "b",
    )
    cid = int(rep["id"])
    assert rec_tree.on_tree(cn, "mail", pid)
    assert rec_tree.has_parent(cn, "mail", cid)
    crumbs = rec_mail.tree_crumbs(cn, cid)
    assert crumbs.get("root_id") == pid
    assert crumbs.get("parent_id") == pid
    # reply-all: parent sender {a} U parent mail_tos {b}, exclude self b => {a}
    assert {t["deskId"] for t in (rep.get("mail_tos") or [])} == {"a"}


def test_reply_refuses_add_to_and_the_node_verbs_replace_it(cn) -> None:
    seed_names(cn, ("unit", "roster"), ("a", "desk"), ("b", "desk"), ("c", "desk"), ("d", "desk"))
    book = _Book(cn)
    root = rpc._h_send(
        book,
        {"project": "unit", "src": "a", "dst": "b,c", "body": "root"},
        "unit",
        "a",
    )
    rid = int(root["id"])
    from agent_coord.helpers.errors import CoordError

    for k in ("add_to", "remove_to"):
        with pytest.raises(CoordError, match="mill add"):
            rpc._h_reply(book, {"mail_id": rid, "body": "x", "src": "b", k: ["d"]}, "unit", "b")
    rep = rpc._h_reply(book, {"mail_id": rid, "body": "cc d drop c", "src": "b"}, "unit", "b")
    cid = int(rep["id"])
    _node(book, "add", cid, "d", "b")
    _node(book, "remove", cid, "c", "b")
    # reply-all {a,c} (self b excluded); drop c; add d => {a,d}
    assert _desks(cn, cid) == {"a", "d"}
    # parent membership unchanged
    parent_bare = {str(r.get("desk") or "") for r in rec_mail.to_list(cn, rid)}
    assert {"b", "c"} <= parent_bare


def test_send_parent_explicit_dst_one_off(cn) -> None:
    seed_names(cn, ("unit", "roster"), ("a", "desk"), ("b", "desk"), ("c", "desk"), ("x", "desk"))
    book = _Book(cn)
    root = rpc._h_send(
        book,
        {"project": "unit", "src": "a", "dst": "b,c", "body": "root"},
        "unit",
        "a",
    )
    rid = int(root["id"])
    one = rpc._h_send(
        book,
        {
            "src": "a",
            "dst": "x",
            "body": "one-off under root",
            "parent_type": "mail",
            "parent_id": rid,
        },
        "unit",
        "a",
    )
    oid = int(one["id"])
    assert one.get("parent_id") == rid
    assert {t["deskId"] for t in (one.get("mail_tos") or [])} == {"x"}
    parent_bare = {str(r.get("desk") or "") for r in rec_mail.to_list(cn, rid)}
    assert "x" not in parent_bare
    assert rec_tree.has_parent(cn, "mail", oid)


def test_inbox_public_shape_lean_mail(cn) -> None:
    """Agent inbox/send: lean MAIL; mail_tos has deskId+roster+receipt; no opened."""
    seed_names(cn, ("unit", "roster"), ("a", "desk"), ("b", "desk"), ("c", "desk"))
    book = _Book(cn)
    sent = rpc._h_send(
        book,
        {"project": "unit", "src": "a", "dst": "b,c", "body": "shape check"},
        "unit",
        "a",
    )
    mid = int(sent["id"])
    assert "roster_id" not in sent
    assert "src" not in sent and "dst" not in sent and "dests" not in sent and "tos" not in sent
    assert sent.get("sender") == {"deskId": "a", "roster": "unit"}  # echo = stored letter
    assert isinstance(sent.get("mail_tos"), list) and sent["mail_tos"]
    for t in sent["mail_tos"]:
        assert set(t.keys()) == {"deskId", "receipt"}
        assert "opened" not in t
    inbox = rpc._h_inbox(
        book,
        {"dst": "b", "no_mark": True, "all": True, "limit": 50},
        "unit",
        "b",
    )
    hit = next((r for r in inbox if int(r.get("id") or 0) == mid), None)
    assert hit is not None, "sent mail missing from inbox"
    assert "roster_id" not in hit
    assert "roster" not in hit
    assert "src" not in hit and "dst" not in hit and "dests" not in hit and "tos" not in hit
    assert "read" not in hit and "opened" not in hit
    assert hit.get("sender") == {"deskId": "a", "roster": "unit"}  # SP insert stamps project
    tos = hit.get("mail_tos") or []
    assert isinstance(tos, list) and len(tos) >= 2
    desks = {t["deskId"] for t in tos}
    assert {"b", "c"} <= desks
    for t in tos:
        assert set(t.keys()) == {"deskId", "receipt"}
        assert isinstance(t["receipt"], int)
        if t.get("roster") is not None:
            assert not str(t["roster"]).isdigit()
    # Multi-To without --room stays off-tree (Host room needs --room)
    assert hit.get("room") is not True


def test_floor_mailbox_lean_mail(cn) -> None:
    """Floor mailbox uses lean public MAIL (mail_tos, no letter roster/opened)."""
    from agent_coord.server.records import floor as rec_floor

    seed_names(cn, ("unit", "roster"), ("a", "desk"), ("b", "desk"))
    book = _Book(cn)
    sent = rpc._h_send(
        book,
        {"project": "unit", "src": "a", "dst": "b", "body": "floor shape"},
        "unit",
        "a",
    )
    mid = int(sent["id"])
    f = rec_floor.floor(cn, "unit", parts=["mail"])
    hit = next((r for r in (f.get("mailbox") or []) if int(r.get("id") or 0) == mid), None)
    assert hit is not None
    assert "roster_id" not in hit
    assert "roster" not in hit
    assert "src" not in hit and "tos" not in hit and "dests" not in hit
    assert hit.get("sender") == {"deskId": "a", "roster": "unit"}  # SP insert stamps project
    tos = hit.get("mail_tos") or []
    assert any(t.get("deskId") == "b" for t in tos)
    for t in tos:
        assert set(t.keys()) == {"deskId", "receipt"}
        assert "opened" not in t



def test_mail_thread_full_chain(cn) -> None:
    """mail-thread returns lean chain for multi-To room + reply."""
    seed_names(cn, ("unit", "roster"), ("a", "desk"), ("b", "desk"), ("c", "desk"))
    book = _Book(cn)
    root = rpc._h_send(
        book,
        {"project": "unit", "src": "a", "dst": "b,c", "body": "root"},
        "unit",
        "a",
    )
    rid = int(root["id"])
    rep = rpc._h_reply(
        book,
        {"mail_id": rid, "body": "child", "src": "b"},
        "unit",
        "b",
    )
    cid = int(rep["id"])
    got = rpc._h_mail_thread(book, {"scope": "room", "mail_id": rid}, "unit", "a")
    assert got["id"] == rid
    assert got.get("root_id") == rid
    assert isinstance(got.get("chain"), list)
    ids = [int(m["id"]) for m in got["chain"]]
    assert rid in ids and cid in ids
    for m in got["chain"]:
        assert set(m.keys()) >= {"id", "created", "sender", "body", "mail_tos"}
        assert "opened" not in m
        assert "src" not in m and "dests" not in m and "tos" not in m
        for t in m["mail_tos"]:
            assert set(t.keys()) == {"deskId", "receipt"}
            assert "opened" not in t
    # recipient can fetch
    got_b = rpc._h_mail_thread(book, {"scope": "room", "mail_id": cid}, "unit", "b")
    assert {int(m["id"]) for m in got_b["chain"]} >= {rid, cid}


def test_mail_thread_off_tree_single(cn) -> None:
    """Off-tree single-dest mail: chain is [self]."""
    seed_names(cn, ("unit", "roster"), ("a", "desk"), ("b", "desk"))
    book = _Book(cn)
    sent = rpc._h_send(
        book,
        {"project": "unit", "src": "a", "dst": "b", "body": "plain"},
        "unit",
        "a",
    )
    mid = int(sent["id"])
    got = rpc._h_mail_thread(book, {"mail_id": mid}, "unit", "b")
    assert got["id"] == mid
    assert len(got["chain"]) == 1
    assert got["chain"][0]["id"] == mid
    assert got["chain"][0]["sender"] == {"deskId": "a", "roster": "unit"}  # SP insert stamps project


def test_mail_thread_stranger_refused(cn) -> None:
    from agent_coord.helpers.errors import CoordError

    seed_names(cn, ("unit", "roster"), ("a", "desk"), ("b", "desk"), ("z", "desk"))
    book = _Book(cn)
    sent = rpc._h_send(
        book,
        {"project": "unit", "src": "a", "dst": "b", "body": "private"},
        "unit",
        "a",
    )
    mid = int(sent["id"])
    with pytest.raises(CoordError) as ei:
        rpc._h_mail_thread(book, {"mail_id": mid}, "unit", "z")
    msg = str(ei.value).lower()
    # #sec S-3: a plain (off-tree) letter is private; no reply-to-join, only mill add.
    assert "private" in msg and "mill add" in msg
    assert "mill reply" not in msg


def test_mail_thread_after_filters_newer(cn) -> None:
    """--after returns same TREE envelope; chain msgs with id > after."""
    seed_names(cn, ("unit", "roster"), ("a", "desk"), ("b", "desk"), ("c", "desk"))
    book = _Book(cn)
    root = rpc._h_send(
        book,
        {"project": "unit", "src": "a", "dst": "b,c", "body": "root"},
        "unit",
        "a",
    )
    rid = int(root["id"])
    r1 = rpc._h_reply(book, {"mail_id": rid, "body": "one", "src": "b"}, "unit", "b")
    r2 = rpc._h_reply(book, {"mail_id": rid, "body": "two", "src": "c"}, "unit", "c")
    id1, id2 = int(r1["id"]), int(r2["id"])
    full = rpc._h_mail_thread(book, {"scope": "room", "mail_id": rid}, "unit", "a")
    assert {int(m["id"]) for m in full["chain"]} >= {rid, id1, id2}
    got = rpc._h_mail_thread(book, {"mail_id": rid, "after": rid}, "unit", "a")
    assert got.get("tree") == full.get("tree")
    assert got.get("root_id") == full.get("root_id")
    ids = [int(m["id"]) for m in got["chain"]]
    assert rid not in ids
    assert id1 in ids and id2 in ids
    assert all(i > rid for i in ids)
    mid = rpc._h_mail_thread(book, {"mail_id": rid, "after": id1}, "unit", "a")
    assert [int(m["id"]) for m in mid["chain"]] == [i for i in ids if i > id1]
    empty = rpc._h_mail_thread(book, {"mail_id": rid, "after": id2}, "unit", "a")
    assert empty["chain"] == []
    assert empty.get("tree") == full.get("tree")


def test_mail_thread_after_missing_coorderror(cn) -> None:
    """Bad/missing after (not on same TREE/chain) -> clear CoordError."""
    from agent_coord.helpers.errors import CoordError

    seed_names(cn, ("unit", "roster"), ("a", "desk"), ("b", "desk"), ("c", "desk"))
    book = _Book(cn)
    root = rpc._h_send(
        book,
        {"project": "unit", "src": "a", "dst": "b,c", "body": "room"},
        "unit",
        "a",
    )
    rid = int(root["id"])
    other = rpc._h_send(
        book,
        {"project": "unit", "src": "a", "dst": "b", "body": "plain other"},
        "unit",
        "a",
    )
    oid = int(other["id"])
    with pytest.raises(CoordError) as ei:
        rpc._h_mail_thread(book, {"mail_id": rid, "after": oid}, "unit", "a")
    assert "after" in str(ei.value).lower()
    assert "same" in str(ei.value).lower() or "chain" in str(ei.value).lower()
    with pytest.raises(CoordError) as ei2:
        rpc._h_mail_thread(book, {"mail_id": rid, "after": 999999999}, "unit", "a")
    assert "after" in str(ei2.value).lower()


def test_mail_thread_after_zero_full_chain(cn) -> None:
    """Omit / after=0 => full chain (same as no after)."""
    seed_names(cn, ("unit", "roster"), ("a", "desk"), ("b", "desk"), ("c", "desk"))
    book = _Book(cn)
    root = rpc._h_send(
        book,
        {"project": "unit", "src": "a", "dst": "b,c", "body": "root"},
        "unit",
        "a",
    )
    rid = int(root["id"])
    rpc._h_reply(book, {"mail_id": rid, "body": "child", "src": "b"}, "unit", "b")
    full = rpc._h_mail_thread(book, {"mail_id": rid}, "unit", "a")
    zero = rpc._h_mail_thread(book, {"mail_id": rid, "after": 0}, "unit", "a")
    assert [int(m["id"]) for m in zero["chain"]] == [int(m["id"]) for m in full["chain"]]



def test_mail_thread_latest_id_always(cn) -> None:
    """Envelope always returns latest_id = max id on full chain (stable under --after)."""
    seed_names(cn, ("unit", "roster"), ("a", "desk"), ("b", "desk"), ("c", "desk"))
    book = _Book(cn)
    root = rpc._h_send(
        book,
        {"project": "unit", "src": "a", "dst": "b,c", "body": "root", "name": "catchup-latest"},
        "unit",
        "a",
    )
    rid = int(root["id"])
    r1 = rpc._h_reply(book, {"mail_id": rid, "body": "one", "src": "b"}, "unit", "b")
    r2 = rpc._h_reply(book, {"mail_id": rid, "body": "two", "src": "c"}, "unit", "c")
    id1, id2 = int(r1["id"]), int(r2["id"])
    expect_latest = max(rid, id1, id2)
    full = rpc._h_mail_thread(book, {"mail_id": rid}, "unit", "a")
    assert full["latest_id"] == expect_latest
    after = rpc._h_mail_thread(book, {"mail_id": rid, "after": rid}, "unit", "a")
    assert after["latest_id"] == expect_latest
    assert all(int(m["id"]) > rid for m in after["chain"])
    empty = rpc._h_mail_thread(book, {"mail_id": rid, "after": id2}, "unit", "a")
    assert empty["chain"] == []
    assert empty["latest_id"] == expect_latest


def test_mail_thread_after_includes_sibling_replies(cn) -> None:
    """Catch-up = whole TREE under room (siblings), not one reply branch."""
    seed_names(cn, ("unit", "roster"), ("a", "desk"), ("b", "desk"), ("c", "desk"))
    book = _Book(cn)
    root = rpc._h_send(
        book,
        {"project": "unit", "src": "a", "dst": "b,c", "body": "root", "name": "catchup-sib"},
        "unit",
        "a",
    )
    rid = int(root["id"])
    # Two sibling replies under the same root (not nested under each other)
    s1 = rpc._h_reply(book, {"mail_id": rid, "body": "sib-b", "src": "b"}, "unit", "b")
    s2 = rpc._h_reply(book, {"mail_id": rid, "body": "sib-c", "src": "c"}, "unit", "c")
    id1, id2 = int(s1["id"]), int(s2["id"])
    # Nested child under s1 only
    nest = rpc._h_reply(
        book, {"mail_id": id1, "body": "nested-under-b", "src": "a"}, "unit", "a"
    )
    nid = int(nest["id"])
    got = rpc._h_mail_thread(book, {"mail_id": rid, "after": rid}, "unit", "a")
    ids = {int(m["id"]) for m in got["chain"]}
    # Both siblings + nest (whole TREE), not just one branch
    assert id1 in ids and id2 in ids and nid in ids
    assert rid not in ids
    # Peek via nested node still returns whole TREE catch-up
    via_nest = rpc._h_mail_thread(book, {"mail_id": nid, "after": rid}, "unit", "a")
    assert {int(m["id"]) for m in via_nest["chain"]} == ids
    assert via_nest["latest_id"] == max(rid, id1, id2, nid)


def test_mail_thread_root_cast_omitted_reader(cn) -> None:
    """A reply that drops a desk is hidden from that desk (#191)."""
    seed_names(cn, ("unit", "roster"), ("a", "desk"), ("b", "desk"), ("c", "desk"))
    book = _Book(cn)
    root = rpc._h_send(
        book,
        {"project": "unit", "src": "a", "dst": "b,c", "body": "room-open", "name": "catchup-cast"},
        "unit",
        "a",
    )
    rid = int(root["id"])
    # b replies and removes c from this letter's mail_tos
    rep = rpc._h_reply(book, {"mail_id": rid, "body": "omit-c", "src": "b"}, "unit", "b")
    cid = int(rep["id"])
    _node(book, "remove", cid, "c", "b")
    # Per-mail: c not on reply mail_tos
    assert "c" not in _desks(cn, cid)
    # c is still in the room via the root, and still sees that root letter.
    # The reply that removed c is not shown.
    full_c = rpc._h_mail_thread(book, {"scope": "room", "mail_id": rid}, "unit", "c")
    assert {int(m["id"]) for m in full_c["chain"]} == {rid}
    # The hidden reply is not the latest id and is not in the count (#206).
    assert full_c["latest_id"] == rid
    assert full_c["room_letters"] == 1
    via_rep = rpc._h_mail_thread(book, {"scope": "room", "mail_id": cid}, "unit", "c")
    assert {int(m["id"]) for m in via_rep["chain"]} == {rid}
    after_c = rpc._h_mail_thread(book, {"tree": "catchup-cast", "after": rid}, "unit", "c")
    assert {int(m["id"]) for m in after_c["chain"]} == set()
    assert after_c["latest_id"] == rid


def test_mail_thread_by_tree_name(cn) -> None:
    """The room name resolves to the same chain as the root mail id."""
    seed_names(cn, ("unit", "roster"), ("a", "desk"), ("b", "desk"), ("c", "desk"))
    book = _Book(cn)
    host = "dev-standup-by-tree"
    root = rpc._h_send(
        book,
        {"project": "unit", "src": "a", "dst": "b,c", "body": "root", "name": host},
        "unit",
        "a",
    )
    rid = int(root["id"])
    rpc._h_reply(book, {"mail_id": rid, "body": "child", "src": "b"}, "unit", "b")
    by_id = rpc._h_mail_thread(book, {"scope": "room", "mail_id": rid}, "unit", "a")
    tree_name = str(by_id.get("tree") or "")
    assert tree_name == host
    by_tree = rpc._h_mail_thread(book, {"scope": "room", "tree": tree_name}, "unit", "a")
    assert [int(m["id"]) for m in by_tree["chain"]] == [int(m["id"]) for m in by_id["chain"]]
    assert by_tree.get("root_id") == rid
    # room name is the host string, a stored plan name
    by_bare = rpc._h_mail_thread(book, {"scope": "room", "mail_id": host}, "unit", "b")
    assert [int(m["id"]) for m in by_bare["chain"]] == [int(m["id"]) for m in by_id["chain"]]


def test_mail_thread_counts_skip_hidden_letters(cn) -> None:
    """#206: latest_id, room_letters, and the hint count only visible letters."""
    seed_names(cn, ("unit", "roster"), ("a", "desk"), ("b", "desk"), ("c", "desk"))
    book = _Book(cn)
    root = rpc._h_send(
        book,
        {"project": "unit", "src": "a", "dst": "b,c", "body": "root", "name": "priv-count"},
        "unit",
        "a",
    )
    rid = int(root["id"])
    pub = rpc._h_reply(book, {"mail_id": rid, "body": "public", "src": "a"}, "unit", "a")
    hid = rpc._h_reply(book, {"mail_id": rid, "body": "hidden", "src": "b"}, "unit", "b")
    _node(book, "remove", int(hid["id"]), "c", "b")
    pid, hid_id = int(pub["id"]), int(hid["id"])
    got = rpc._h_mail_thread(book, {"scope": "room", "mail_id": rid}, "unit", "c")
    assert {int(m["id"]) for m in got["chain"]} == {rid, pid}
    assert got["latest_id"] == max(rid, pid)
    assert got["latest_id"] != hid_id
    assert got["room_letters"] == 2
    branch = rpc._h_mail_thread(book, {"mail_id": pid}, "unit", "c")
    assert hid_id not in {int(m["id"]) for m in branch["chain"]}
    assert branch["room_letters"] == 2
    assert branch["latest_id"] == max(rid, pid)
    assert "all 2" in branch["hint"]


def test_reply_joiner_sees_the_room_root(cn) -> None:
    """#209: a desk that joined by replying still sees the root. Other private letters stay hidden."""
    seed_names(cn, ("unit", "roster"), ("a", "desk"), ("b", "desk"), ("c", "desk"))
    book = _Book(cn)
    root = rpc._h_send(
        book,
        {"project": "unit", "src": "a", "dst": "b", "body": "root-only-b", "name": "join-root"},
        "unit",
        "a",
    )
    rid = int(root["id"])
    joined = rpc._h_reply(book, {"mail_id": rid, "body": "c-joins", "src": "c"}, "unit", "c")
    jid = int(joined["id"])
    secret = rpc._h_reply(
        book,
        {"mail_id": rid, "body": "secret", "src": "b", "mail_tos": ["a"]},
        "unit",
        "b",
    )
    sid = int(secret["id"])
    got = rpc._h_mail_thread(book, {"scope": "room", "mail_id": rid}, "unit", "c")
    ids = {int(m["id"]) for m in got["chain"]}
    assert rid in ids and jid in ids
    assert sid not in ids
    assert got["latest_id"] == max(rid, jid)
    assert got["room_letters"] == 2
    whole = rpc._h_mail_thread(book, {"scope": "room", "mail_id": rid}, "unit", "a")
    assert {int(m["id"]) for m in whole["chain"]} == {rid, jid, sid}
    assert whole["room_letters"] == 3
    assert whole["latest_id"] == max(rid, jid, sid)


def test_mail_thread_room_name_over_64_refuses(cn) -> None:
    """#208: a room name longer than p_tree refuses before MySQL 1406."""
    from agent_coord.helpers.errors import CoordError

    seed_names(cn, ("unit", "roster"), ("a", "desk"))
    book = _Book(cn)
    huge = "r" * 65
    with pytest.raises(CoordError) as ei:
        rpc._h_mail_thread(book, {"tree": huge}, "unit", "a")
    msg = str(ei.value)
    assert msg.startswith("mail-thread: no mail room named")
    assert "1406" not in msg
    exact = "e" * 64
    with pytest.raises(CoordError) as ei2:
        rpc._h_mail_thread(book, {"tree": exact}, "unit", "a")
    assert "no mail room named" in str(ei2.value)
    assert "1406" not in str(ei2.value)


def test_mail_thread_unknown_tree_coorderror(cn) -> None:
    from agent_coord.helpers.errors import CoordError

    seed_names(cn, ("unit", "roster"), ("a", "desk"))
    book = _Book(cn)
    with pytest.raises(CoordError) as ei:
        rpc._h_mail_thread(book, {"tree": "no_such_room_zz"}, "unit", "a")
    assert "no mail room" in str(ei.value).lower() or "named" in str(ei.value).lower()


def test_send_mail_tos_roster_sql(cn) -> None:
    """Dest roster is not stored. mail_to keeps the desks and receipt."""
    seed_names(cn, ("unit", "roster"), ("builder", "roster"), ("a", "desk"), ("b", "desk"), ("c", "desk"), ("d", "desk"))
    book = _Book(cn)
    rec = rpc._h_send(
        book,
        {
            "src": "a",
            "body": "tos aff",
            "mail_tos": [
                {"deskId": "b", "roster": "builder"},
                {"deskId": "c", "roster": "unit"},
                {"deskId": "d"},
            ],
        },
        "unit",
        "a",
    )
    assert rec.get("room") is not True  # multi-To without --room = plain
    by = {t["deskId"]: t for t in rec["mail_tos"]}
    assert set(by) == {"b", "c", "d"}
    assert "roster" not in by["b"]
    assert "roster" not in by["c"]
    assert "roster" not in by["d"]
    rows = {str(r.get("desk") or ""): r.get("roster")
            for r in rec_mail.to_list(cn, int(rec["id"]))}
    assert rows["b"] is None
    assert rows["c"] is None
    assert rows["d"] is None


def test_send_cli_default_roster_sql(cn) -> None:
    seed_names(cn, ("unit", "roster"), ("builder", "roster"), ("a", "desk"), ("b", "desk"))
    book = _Book(cn)
    rec = rpc._h_send(
        book,
        {"project": "unit", "src": "a", "dst": "b", "body": "aff default", "roster": "builder"},
        "unit",
        "a",
    )
    assert rec.get("room") is not True
    assert rec["sender"] == {"deskId": "a", "roster": "builder"}
    assert rec["mail_tos"] == [{"deskId": "b", "receipt": 0}]


def test_send_sender_roster_and_reply_reciprocal(cn) -> None:
    """mail.roster_id on send; reply mail_to gets parent sender desk+roster."""
    seed_names(cn, ("unit", "roster"), ("a", "desk"), ("b", "desk"), ("builder", "roster"), ("validator", "roster"))
    book = _Book(cn)
    root = rpc._h_send(
        book,
        {
            "src": "a",
            "dst": "b",
            "body": "tagged",
            "roster": "builder",
        },
        "unit",
        "a",
    )
    rid = int(root["id"])
    assert root["sender"] == {"deskId": "a", "roster": "builder"}
    assert "roster" not in root["mail_tos"][0]
    letter = rec_mail.letter_row(cn, rid)
    assert letter is not None
    assert str(letter.get("sender_roster") or "").endswith("builder") or (
        letter.get("sender_roster") == "builder"
    )
    rep = rpc._h_reply(
        book,
        {"mail_id": rid, "body": "back", "src": "b", "roster": "validator"},
        "unit",
        "b",
    )
    assert {t["deskId"] for t in (rep.get("mail_tos") or [])} == {"a"}
    assert "roster" not in rep["mail_tos"][0]
    assert rep["sender"] == {"deskId": "b", "roster": "validator"}
    cast = rec_mail.room_cast(rep)
    assert {"a", "b"} == {c["deskId"] for c in cast}


def test_tree_mail_returns_every_letter_on_the_tree(cn) -> None:
    """tree-mail returns every letter on the tree, with that letter's roster."""
    from agent_coord.server.records.floor import v1_tree_mail

    seed_names(
        cn,
        ("Office", "roster"),
        ("the-mill", "roster"),
        ("other", "roster"),
        ("a", "desk"),
        ("b", "desk"),
        ("c", "desk"),
    )
    book = _Book(cn)
    root = rpc._h_send(
        book,
        {"project": "Office", "src": "a", "dst": "b", "body": "room root"},
        "Office",
        "a",
    )
    rid = int(root["id"])
    mid = rpc._h_reply(
        book,
        {"project": "the-mill", "mail_id": rid, "body": "room reply", "src": "b"},
        "the-mill",
        "b",
    )
    mid_id = int(mid["id"])
    # This room was opened from a private letter, so c joins by add (#sec S-3).
    rpc._h_add_remove(book, {"verb": "add", "type": "mail", "id": rid, "who": "c"}, "Office", "b")
    leaf = rpc._h_reply(
        book,
        {"project": "other", "mail_id": mid_id, "body": "room leaf", "src": "c"},
        "other",
        "c",
    )
    leaf_id = int(leaf["id"])

    def room_for(project: str) -> list[dict]:
        out = v1_tree_mail(cn, project=project, limit=50, depth=8)
        hits = []
        for tree in out.get("trees") or []:
            nodes = list(tree.get("nodes") or [])
            if any(int(n.get("id") or 0) == rid for n in nodes):
                hits.append(nodes)
        assert len(hits) == 1
        return hits[0]

    for project in ("Office", "the-mill", "other"):
        nodes = room_for(project)
        assert {int(n.get("id") or 0) for n in nodes} == {rid, mid_id, leaf_id}
        aff = {int(n.get("id") or 0): str(n.get("roster_id") or "") for n in nodes}
        assert aff[rid] == "Office"
        assert aff[mid_id] == "the-mill"
        assert aff[leaf_id] == "other"


def test_tree_todo_returns_every_card_on_the_tree(cn) -> None:
    """tree-todo returns every card on the tree, with that card's roster."""
    from agent_coord.server.records import todo as rec_todo
    from agent_coord.server.records.floor import v1_tree_todo

    seed_names(
        cn,
        ("Office", "roster"),
        ("the-mill", "roster"),
        ("other", "roster"),
        ("a", "desk"),
    )
    root = rec_todo.insert(cn, "Office", "a", "open", '{"doing":"root"}')
    rid = int(root[0]["id"])
    rec_tree.create(cn, "unit-todo-aff", "todo", rid)
    mid = rec_todo.insert(cn, "the-mill", "a", "open", '{"doing":"mid"}')
    mid_id = int(mid[0]["id"])
    rec_tree.add(cn, "todo", rid, "todo", mid_id, tree="unit-todo-aff")
    leaf = rec_todo.insert(cn, "other", "a", "open", '{"doing":"leaf"}')
    leaf_id = int(leaf[0]["id"])
    rec_tree.add(cn, "todo", mid_id, "todo", leaf_id, tree="unit-todo-aff")

    def aff_for(project: str) -> dict[int, str]:
        out = v1_tree_todo(cn, project=project, limit=50, depth=8)
        found: dict[int, str] = {}
        for tree in out.get("trees") or []:
            if str(tree.get("name") or "") != "unit-todo-aff":
                continue
            for node in tree.get("nodes") or []:
                found[int(node.get("id") or 0)] = str(node.get("roster_id") or "")
        return found

    for project in ("Office", "the-mill", "other"):
        aff = aff_for(project)
        assert set(aff) == {rid, mid_id, leaf_id}
        assert aff[rid] == "Office"
        assert aff[mid_id] == "the-mill"
        assert aff[leaf_id] == "other"


def test_room_participant_on_later_letter_reads_room(cn) -> None:
    """A desk added on a later letter (not the root cast) can mail-thread the room."""
    from agent_coord.helpers.errors import CoordError

    seed_names(
        cn, ("unit", "roster"), ("ra", "desk"), ("rb", "desk"), ("rc", "desk"), ("rz", "desk")
    )
    book = _Book(cn)
    slug = "participants-room"
    root = rpc._h_send(book, {"project": "unit", "src": "ra", "dst": "rb", "body": "root", "name": slug}, "unit", "ra")
    rid = int(root["id"])
    # rb adds rc at its reply (mill add mail:ID rc); rc is not on the root letter.
    rep = rpc._h_reply(book, {"mail_id": rid, "body": "bring rc"}, "unit", "rb")
    cid = int(rep["id"])
    _node(book, "add", cid, "rc", "rb")
    assert _desks(cn, cid) == {"ra", "rc"}
    # rc was not on the root letter. #209 still shows that root to a participant.
    # The reply that named rc is visible, and the room read is not refused.
    for handle in ({"tree": slug}, {"mail_id": rid}, {"mail_id": cid}, {"mail_id": slug}):
        got = rpc._h_mail_thread(book, dict(handle, scope="room"), "unit", "rc")
        assert {int(m["id"]) for m in got["chain"]} == {rid, cid}
    got_b = rpc._h_mail_thread(book, {"mail_id": rid, "scope": "room"}, "unit", "rb")
    assert {int(m["id"]) for m in got_b["chain"]} == {rid, cid}
    # outsider still refused, by name and by id
    for handle in ({"tree": slug}, {"mail_id": rid}, {"mail_id": cid}):
        with pytest.raises(CoordError) as ei:
            rpc._h_mail_thread(book, dict(handle), "unit", "rz")
        assert "not a participant" in str(ei.value).lower()


def test_room_read_hides_a_letter_the_desk_was_not_on(cn) -> None:
    """#191: --room hides a letter addressed only to one other desk."""
    seed_names(
        cn, ("unit", "roster"), ("ra", "desk"), ("rb", "desk"), ("rc", "desk")
    )
    book = _Book(cn)
    slug = "private-room-191"
    root = rpc._h_send(
        book, {"project": "unit", "src": "ra", "dst": "rb", "body": "root", "name": slug}, "unit", "ra"
    )
    rid = int(root["id"])
    brought = rpc._h_reply(book, {"mail_id": rid, "body": "bring rc"}, "unit", "rb")
    bid = int(brought["id"])
    _node(book, "add", bid, "rc", "rb")
    private = rpc._h_reply(book, {"mail_id": rid, "body": "only rc"}, "unit", "rb")
    pid = int(private["id"])
    _node(book, "remove", pid, "ra", "rb")
    assert _desks(cn, pid) == {"rc"}

    def seen(desk: str) -> set[int]:
        got = rpc._h_mail_thread(
            book, {"tree": slug, "scope": "room"}, "unit", desk
        )
        return {int(m["id"]) for m in got["chain"]}

    assert seen("ra") == {rid, bid}
    # rc joined on a later letter. The root is shown (#209). The private letter stays.
    assert seen("rc") == {rid, bid, pid}
    assert seen("rb") == {rid, bid, pid}
    branch = rpc._h_mail_thread(book, {"mail_id": pid, "scope": "branch"}, "unit", "ra")
    assert pid not in {int(m["id"]) for m in branch["chain"]}
    assert all("only rc" not in str(m.get("body") or "") for m in branch["chain"])


def test_room_reply_all_reaches_every_participant(cn) -> None:
    """A plain reply to any letter in a room goes to all participants minus self."""
    seed_names(
        cn,
        ("unit", "roster"),
        ("pa", "desk"),
        ("pb", "desk"),
        ("pc", "desk"),
        ("pd", "desk"),
        ("pz", "desk"),
    )
    book = _Book(cn)
    root = rpc._h_send(
        book, {"project": "unit", "src": "pa", "dst": "pb", "body": "root", "name": "reply-all-room"}, "unit", "pa"
    )
    rid = int(root["id"])
    r1 = rpc._h_reply(book, {"mail_id": rid, "body": "add pc"}, "unit", "pb")
    _node(book, "add", int(r1["id"]), "pc", "pb")
    r2 = rpc._h_reply(book, {"mail_id": int(r1["id"]), "body": "add pd"}, "unit", "pc")
    _node(book, "add", int(r2["id"]), "pd", "pc")
    # pc replies to the root letter (pc was not on it): reaches pa, pb, pd.
    r3 = rpc._h_reply(book, {"mail_id": rid, "body": "to the room"}, "unit", "pc")
    assert {t["deskId"] for t in r3["mail_tos"]} == {"pa", "pb", "pd"}
    # pa replies plain to pd's branch letter: every participant but pa.
    r4 = rpc._h_reply(book, {"mail_id": int(r2["id"]), "body": "all hands"}, "unit", "pa")
    assert {t["deskId"] for t in r4["mail_tos"]} == {"pb", "pc", "pd"}
    assert "pz" not in {t["deskId"] for t in r4["mail_tos"]}
    # mill remove at the new letter trims the room cast there
    r5 = rpc._h_reply(book, {"mail_id": rid, "body": "not pd"}, "unit", "pb")
    _node(book, "remove", int(r5["id"]), "pd", "pb")
    assert _desks(cn, int(r5["id"])) == {"pa", "pc"}


def test_send_name_existing_room_hint_names_root(cn) -> None:
    from agent_coord.helpers.errors import CoordError

    seed_names(cn, ("unit", "roster"), ("ha", "desk"), ("hb", "desk"))
    book = _Book(cn)
    slug = "hint-room"
    root = rpc._h_send(book, {"project": "unit", "src": "ha", "dst": "hb", "body": "first", "name": slug}, "unit", "ha")
    rid = int(root["id"])
    from agent_coord.server.records.db import scalar

    top = int(scalar(cn, "SELECT MAX(id) FROM mail") or 0)
    with pytest.raises(CoordError) as ei:
        rpc._h_send(book, {"project": "unit", "src": "hb", "dst": "ha", "body": "dup", "name": slug}, "unit", "hb")
    assert f"room '{slug}' exists; post in it with: mill reply {rid} --body-file PATH" in str(ei.value)
    # refused before insert: no orphan letter
    assert int(scalar(cn, "SELECT MAX(id) FROM mail") or 0) == top
