# -*- coding: utf-8 -*-
"""mail-thread read scopes (#148) and open-by-reply join (#149).

Room shape used here (nested replies):
    root (a -> b,c)
      r1 (b)
        r1a (c)
      r2 (c)
        r2a (a)
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.sql

from agent_coord.helpers.errors import CoordError
from agent_coord.server.api.mill import rpc
from tests.server.records.conftest import seed_names
from tests.server.records.test_room_reply import _Book


def _ids(out: dict) -> list[int]:
    return [int(m["id"]) for m in out.get("chain") or []]


def _room(cn, tag: str) -> dict:
    a, b, c = f"{tag}a", f"{tag}b", f"{tag}c"
    seed_names(cn, ("unit", "roster"), (a, "desk"), (b, "desk"), (c, "desk"))
    book = _Book(cn)
    root = int(rpc._h_send(book, {"src": a, "dst": f"{b},{c}", "body": "root", "name": f"{tag}-room"}, "unit", a)["id"])
    r1 = int(rpc._h_reply(book, {"mail_id": root, "body": "r1"}, "unit", b)["id"])
    r1a = int(rpc._h_reply(book, {"mail_id": r1, "body": "r1a"}, "unit", c)["id"])
    r2 = int(rpc._h_reply(book, {"mail_id": root, "body": "r2"}, "unit", c)["id"])
    r2a = int(rpc._h_reply(book, {"mail_id": r2, "body": "r2a"}, "unit", a)["id"])
    return {"book": book, "a": a, "b": b, "c": c, "name": f"{tag}-room",
            "root": root, "r1": r1, "r1a": r1a, "r2": r2, "r2a": r2a}


def test_branch_is_default_for_mail_id(cn) -> None:
    r = _room(cn, "br")
    got = rpc._h_mail_thread(r["book"], {"mail_id": r["r1a"]}, "unit", r["a"])
    assert got["scope"] == "branch"
    assert _ids(got) == [r["root"], r["r1"], r["r1a"]]
    assert got["room_letters"] == 5
    assert got["latest_id"] == r["r2a"]
    assert "--room" in got["hint"]
    # root alone: branch is just the root, hint names --subtree for the 4 under it
    top = rpc._h_mail_thread(r["book"], {"mail_id": r["root"]}, "unit", r["a"])
    assert _ids(top) == [r["root"]]
    assert top["replies_under"] == 4
    assert "--subtree" in top["hint"]


def test_reread_of_a_reply_omits_the_parent(cn) -> None:
    """#212: a second read of a reply is that letter alone. A later sibling skips the root."""
    r = _room(cn, "rr")
    first = rpc._h_mail_thread(r["book"], {"mail_id": r["r1a"]}, "unit", r["a"])
    assert r["root"] in _ids(first)
    again = rpc._h_mail_thread(r["book"], {"mail_id": r["r1a"]}, "unit", r["a"])
    assert _ids(again) == [r["r1a"]]
    sib = rpc._h_mail_thread(r["book"], {"mail_id": r["r2a"]}, "unit", r["a"])
    assert r["root"] not in _ids(sib)
    assert r["r2a"] in _ids(sib)


def test_later_read_omits_served_ancestors(cn) -> None:
    """#190: once a desk has been served a letter, the next read leaves it out."""
    r = _room(cn, "sv")
    first = rpc._h_mail_thread(r["book"], {"mail_id": r["r1a"]}, "unit", r["a"])
    assert _ids(first) == [r["root"], r["r1"], r["r1a"]]
    later = rpc._h_mail_thread(r["book"], {"mail_id": r["r2a"]}, "unit", r["a"])
    assert r["root"] not in _ids(later)
    assert r["r1a"] not in _ids(later)
    assert r["r2a"] in _ids(later)


def test_subtree_scope(cn) -> None:
    r = _room(cn, "st")
    got = rpc._h_mail_thread(r["book"], {"mail_id": r["r2"], "scope": "subtree"}, "unit", r["b"])
    assert got["scope"] == "subtree"
    assert _ids(got) == [r["r2"], r["r2a"]]


def test_room_scope_is_whole_room(cn) -> None:
    r = _room(cn, "rm")
    want = [r["root"], r["r1"], r["r1a"], r["r2"], r["r2a"]]
    got = rpc._h_mail_thread(r["book"], {"mail_id": r["r1a"], "scope": "room"}, "unit", r["a"])
    assert got["scope"] == "room"
    assert _ids(got) == want
    assert "hint" not in got


def test_scope_all_is_refused(cn) -> None:
    r = _room(cn, "rmall")
    with pytest.raises(CoordError, match="not a flag"):
        rpc._h_mail_thread(
            r["book"], {"mail_id": r["r1a"], "scope": "all"}, "unit", r["a"]
        )


def test_room_name_without_flag_is_summary(cn) -> None:
    r = _room(cn, "sm")
    got = rpc._h_mail_thread(r["book"], {"tree": r["name"]}, "unit", r["a"])
    assert got["scope"] == "summary"
    assert _ids(got) == [r["root"], r["r1a"], r["r2"], r["r2a"]]
    assert got["room_letters"] == 5
    assert f"mill mail-thread {r['name']} --room" in got["hint"]
    full = rpc._h_mail_thread(r["book"], {"tree": r["name"], "scope": "room"}, "unit", r["a"])
    assert len(_ids(full)) == 5


def test_summary_trims_bodies_and_drops_mail_tos(cn) -> None:
    r = _room(cn, "tb")
    long = "L" * 400
    rpc._h_reply(r["book"], {"mail_id": r["root"], "body": long}, "unit", r["b"])
    got = rpc._h_mail_thread(r["book"], {"tree": r["name"]}, "unit", r["a"])
    assert got["scope"] == "summary"
    assert any(letter.get("body_trunc") is True and len(letter["body"]) == 256 for letter in got["chain"])
    assert all("mail_tos" not in letter for letter in got["chain"])
    full = rpc._h_mail_thread(r["book"], {"tree": r["name"], "scope": "room"}, "unit", r["a"])
    assert any(letter.get("body") == long for letter in full["chain"])
    assert any(letter.get("mail_tos") for letter in full["chain"])


def test_after_implies_room_and_works_with_scopes(cn) -> None:
    r = _room(cn, "af")
    got = rpc._h_mail_thread(r["book"], {"mail_id": r["root"], "after": r["r1a"]}, "unit", r["a"])
    assert got["scope"] == "room"
    assert _ids(got) == [r["r2"], r["r2a"]]
    by_name = rpc._h_mail_thread(r["book"], {"tree": r["name"], "after": r["r1"]}, "unit", r["a"])
    assert _ids(by_name) == [r["r1a"], r["r2"], r["r2a"]]
    sub = rpc._h_mail_thread(
        r["book"], {"mail_id": r["r1"], "scope": "subtree", "after": r["r1"]}, "unit", r["a"]
    )
    assert _ids(sub) == [r["r1a"]]
    with pytest.raises(CoordError):
        rpc._h_mail_thread(r["book"], {"mail_id": r["root"], "scope": "bogus"}, "unit", r["a"])


def test_outsider_refusal_names_join_route(cn) -> None:
    r = _room(cn, "rf")
    seed_names(cn, ("rfz", "desk"))
    with pytest.raises(CoordError) as ei:
        rpc._h_mail_thread(r["book"], {"mail_id": r["r1a"]}, "unit", "rfz")
    msg = str(ei.value)
    assert f"run mill reply {r['root']} --body-file PATH to join" in msg
    assert "<body>" not in msg
    assert "ask a participant to mill add you" in msg


def test_exchange_reply_reads_stay_small(cn) -> None:
    """A 4-and-4 exchange: each reply-read is only letters not yet served (#190)."""
    tag = "cx"
    a, b = f"{tag}a", f"{tag}b"
    seed_names(cn, ("unit", "roster"), (a, "desk"), (b, "desk"))
    book = _Book(cn)
    root = int(rpc._h_send(
        book, {"src": a, "dst": b, "body": "root", "name": f"{tag}-room"}, "unit", a
    )["id"])

    def read(who: str, mid: int, **extra) -> list[int]:
        body = {"mail_id": mid}
        body.update(extra)
        return _ids(rpc._h_mail_thread(book, body, "unit", who))

    assert read(a, root) == [root]
    assert read(b, root) == [root]
    last = root
    # a already sent the root. Three more from a and four from b.
    for i, who in enumerate((b, a, b, a, b, a, b)):
        last = int(rpc._h_reply(book, {"mail_id": last, "body": f"m{i}"}, "unit", who)["id"])
        reader = a if who == b else b
        got = read(reader, last)
        # The new letter only. A letter the reader sent stays off this read (#190, #222).
        assert got == [last], got
    full = read(a, last, scope="full")
    assert len(full) == 8
    assert len(full) > 3
    room = read(a, last, scope="room")
    assert len(room) == 8


def test_ensure_adds_tree_read_without_wipe(cn) -> None:
    """Existing book: ensure creates tree_read and does not wipe (#155)."""
    from agent_coord.install import migrate

    cur = cn.cursor()
    cur.execute("DROP TABLE IF EXISTS tree_read")
    cn.commit()
    cur.close()
    out = migrate.ensure(cn)
    assert "tree_read" in (out.get("applied") or [])
    cur = cn.cursor()
    cur.execute("SHOW TABLES LIKE 'tree_read'")
    assert cur.fetchone()
    cur.close()
    again = migrate.ensure(cn)
    assert "tree_read" not in (again.get("applied") or [])


def test_tree_read_keys_on_tree_name_id(cn) -> None:
    """The cursor row is (desk name id, tree.name_id), not the root mail id."""
    from agent_coord.server.records import mail as rec_mail

    tag = "tk"
    a, b = f"{tag}a", f"{tag}b"
    seed_names(cn, ("unit", "roster"), (a, "desk"), (b, "desk"))
    book = _Book(cn)
    root = int(rpc._h_send(
        book, {"src": a, "dst": b, "body": "root", "name": f"{tag}-room"}, "unit", a
    )["id"])
    rpc._h_mail_thread(book, {"mail_id": root}, "unit", b)
    tid = rec_mail.room_tree_id(cn, root)
    assert tid
    cur = cn.cursor()
    cur.execute("SELECT type, name FROM name WHERE id = %s", (tid,))
    assert cur.fetchone() == ("tree", f"{tag}-room")
    cur.execute(
        "SELECT r.tree_id, r.last_id FROM tree_read r JOIN name d ON d.id = r.desk_id "
        "WHERE d.type = 'desk' AND d.name = %s",
        (b,),
    )
    assert cur.fetchall() == [(tid, root)]
    cur.close()


def test_tree_read_fk_refuses_unknown_tree(cn) -> None:
    """fk_tree_read_tree: a tree_id that is not a name row is refused."""
    import mysql.connector

    seed_names(cn, ("fkd", "desk"))
    cur = cn.cursor()
    cur.execute("SELECT id FROM name WHERE type = 'desk' AND name = 'fkd'")
    did = int(cur.fetchone()[0])
    cur.execute("SELECT IFNULL(MAX(id), 0) + 100000 FROM name")
    bogus = int(cur.fetchone()[0])
    with pytest.raises(mysql.connector.Error) as ei:
        cur.execute(
            "INSERT INTO tree_read (desk_id, tree_id, last_id) VALUES (%s, %s, 1)",
            (did, bogus),
        )
    assert getattr(ei.value, "errno", None) == 1452
    cn.rollback()
    cur.close()


def test_outsider_reply_joins_gets_push_and_reads_branch(cn, monkeypatch) -> None:
    """Office desk never on the room replies, then hears later letters and reads."""
    r = _room(cn, "oj")
    seed_names(cn, ("ojz", "desk"))
    pushed: list[tuple[str, str, int]] = []

    def _emit(_cn, desk, kind, payload, **kw):
        pushed.append((str(desk), str(kind), int(payload.get("id") or 0)))
        return "sent"

    monkeypatch.setattr("agent_coord.server.push.emit", _emit)
    # outsider replies to r1 without being a sender or recipient: allowed
    mine = int(rpc._h_reply(r["book"], {"mail_id": r["r1"], "body": "outsider"}, "unit", "ojz")["id"])
    # a later reply-all letter by a room desk reaches the outsider with push
    later = rpc._h_reply(r["book"], {"mail_id": r["root"], "body": "later"}, "unit", r["a"])
    lid = int(later["id"])
    assert "ojz" in {t["deskId"] for t in later["mail_tos"]}
    assert ("ojz", "mail", lid) in pushed
    # #209: the room root is shown to the joiner.
    # #219: room letters sent before the join are shown too. A narrowed letter stays hidden.
    got = rpc._h_mail_thread(r["book"], {"mail_id": mine}, "unit", "ojz")
    assert _ids(got) == [r["root"], r["r1"], mine]
    full = rpc._h_mail_thread(r["book"], {"mail_id": lid, "scope": "room"}, "unit", "ojz")
    assert set(_ids(full)) == {r["root"], r["r1"], r["r1a"], r["r2"], r["r2a"], mine, lid}
    assert full["room_letters"] == len(set(_ids(full)))
