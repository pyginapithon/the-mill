"""#274: a todo by ROSTER/NEED, send word checks, sender left out, add roster names desks.

Real book. Each refusal is one line and changes nothing.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from agent_coord.helpers.errors import CoordError
from agent_coord.server.api.mill.rpc import _card_ref_id, _h_add_remove, _h_member, _h_send
from agent_coord.server.records import todo as rec_todo
from agent_coord.server.records.db import scalar
from tests.server.records.conftest import seed_names

pytestmark = pytest.mark.sql

R = "cl274"
R2 = "cl274-two"


def _c(cn):
    return SimpleNamespace(_cn=cn)


def _counts(cn):
    return tuple(scalar(cn, f"SELECT COUNT(*) FROM {t}") for t in ("mail", "mail_to", "watcher", "member"))


@pytest.fixture(scope="module")
def board(cn):
    seed_names(cn, (R, "roster"), (R2, "roster"), ("cl_a", "desk"), ("cl_b", "desk"), ("cl_c", "desk"))
    for d in ("cl_a", "cl_b"):
        _h_member(_c(cn), {"verb": "member-add", "group": R, "desk": d}, R, d)
    tid = int(rec_todo.insert(cn, R, "cl_a", "open", '{"slug": "fix-login", "doing": "login 500"}')[0]["id"])
    return {"tid": tid}


def test_ref_resolves_to_the_card_id(cn, board):
    assert _card_ref_id(cn, {"type": "todo", "ref": f"{R}/fix-login"}, "add") == board["tid"]


def test_no_ref_is_zero(cn, board):
    assert _card_ref_id(cn, {"type": "todo"}, "add") == 0


@pytest.mark.parametrize(
    "ref,typ,msg",
    [
        (f"{R}/no-such", "todo", f"add: no card no-such in {R}"),
        ("cl-nobody/fix-login", "todo", "add: no roster cl-nobody"),
        (f"{R}/", "todo", "add: give the todo as ROSTER/NEED"),
        ("/fix-login", "todo", "add: give the todo as ROSTER/NEED"),
        (f"{R}/12", "todo", "add: 12 is a todo id"),
        (f"{R}/fix-login", "score", "add: only a todo (ROSTER/NEED) or a hold (its name) goes by name"),
        ("cl-no-such-hold", "hold", "add: no hold named cl-no-such-hold"),
        (f"{R}/" + "x" * 65, "todo", "add: give the todo as ROSTER/NEED"),
    ],
)
def test_bad_ref_refused_one_line(cn, board, ref, typ, msg):
    before = _counts(cn)
    with pytest.raises(CoordError) as ei:
        _card_ref_id(cn, {"type": typ, "ref": ref}, "add")
    assert str(ei.value).startswith(msg)
    assert "\n" not in str(ei.value)
    assert _counts(cn) == before


def test_label_command_named_as_typed(cn, board):
    with pytest.raises(CoordError, match="^label: no card"):
        _card_ref_id(cn, {"type": "todo", "ref": f"{R}/nope"}, "label-add")


def test_watch_and_unwatch_by_ref(cn, board):
    w0 = scalar(cn, "SELECT COUNT(*) FROM watcher")
    body = {"verb": "add", "type": "todo", "ref": f"{R}/fix-login"}
    _h_add_remove(_c(cn), body, R, "cl_c")
    assert scalar(cn, "SELECT COUNT(*) FROM watcher") == w0 + 1
    _h_add_remove(_c(cn), dict(body, verb="remove"), R, "cl_c")
    assert scalar(cn, "SELECT COUNT(*) FROM watcher") == w0


def _send(cn, tos, owner="cl_a"):
    return _h_send(_c(cn), {"verb": "send", "body": "hello", "mail_tos": tos}, R, owner)


@pytest.mark.parametrize(
    "name,said,msg",
    [
        ("cl_b", "roster", "send: cl_b is a desk, not a roster; say: send desk cl_b"),
        (R, "desk", f"send: {R} is a roster, not a desk; say: send roster {R}"),
        ("cl-ghost", "desk", "send: no desk cl-ghost"),
        ("cl-ghost", "roster", "send: no roster cl-ghost"),
        ("cl_b", "room", "send: 'room' is not desk or roster"),
    ],
)
def test_send_word_must_match_type(cn, board, name, said, msg):
    before = _counts(cn)
    with pytest.raises(CoordError) as ei:
        _send(cn, [{"deskId": name, "kind": said}])
    assert str(ei.value) == msg
    assert _counts(cn) == before



def _to_names(cn, mid):
    cur = cn.cursor(buffered=True)
    cur.execute("SELECT n.name FROM mail_to t JOIN name n ON n.id = t.desk_id WHERE t.type='mail' AND t.id=%s", (mid,))
    out = sorted(r[0] for r in cur.fetchall())
    cur.close()
    return out


def test_send_roster_leaves_sender_out_and_says_so(cn, board):
    rec = _send(cn, [{"deskId": R, "kind": "roster"}])
    assert _to_names(cn, int(rec["id"])) == ["cl_b"]
    assert "cl_a" in rec["note"] and "left out" in rec["note"] and R in rec["note"]
    assert rec["note"].startswith("sender: excluded")


def test_send_roster_without_sender_says_not_a_member(cn, board):
    rec = _send(cn, [{"deskId": R, "kind": "roster"}], owner="cl_c")
    assert _to_names(cn, int(rec["id"])) == ["cl_a", "cl_b"]
    assert rec["note"] == f"sender: not a member of roster {R}; it went to its 2 member(s)"


def test_send_plain_desk_has_no_sender_note(cn, board):
    rec = _send(cn, [{"deskId": "cl_b", "kind": "desk"}], owner="cl_c")
    assert "note" not in rec


def test_send_word_ok_plain_desk(cn, board):
    rec = _send(cn, [{"deskId": "cl_b", "kind": "desk"}])
    assert _to_names(cn, int(rec["id"])) == ["cl_b"]


def test_send_roster_sender_alone(cn, board):
    seed_names(cn, ("cl274-solo", "roster"))
    _h_member(_c(cn), {"verb": "member-add", "group": "cl274-solo", "desk": "cl_c"}, R, "cl_c")
    rec = _send(cn, [{"deskId": "cl274-solo", "kind": "roster"}], owner="cl_c")
    assert "only member" in rec["note"]


def test_add_roster_reply_names_the_desk(cn, board):
    rows = _h_member(_c(cn), {"verb": "member-add", "group": R2, "desk": "cl_c"}, R2, "cl_c")
    assert rows and all(r["desk"] == "cl_c" and r["roster"] == R2 for r in rows)
