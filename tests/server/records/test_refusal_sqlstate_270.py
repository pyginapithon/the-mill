"""#270: every add/remove refusal is one plain line (no `1644 (45000):` prefix).

Real book: the SIGNAL refusals from the mail node procedures come back as CoordError
text only, and nothing changes. A watcher on mail is refused by name, not by the ENUM.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from agent_coord.helpers.errors import CoordError
from agent_coord.server.api.mill.rpc import _h_add_remove
from agent_coord.server.records import mail as rec_mail
from agent_coord.server.records import tree as rec_tree
from agent_coord.server.records import watcher as rec_w
from agent_coord.server.records.db import scalar
from tests.server.records.conftest import seed_names

pytestmark = pytest.mark.sql

R = "rf270"


def _go(cn, command, typ, nid, who="", owner="rf_a"):
    body = {"verb": command, "type": typ, "id": nid}
    if who:
        body["who"] = who
    return _h_add_remove(SimpleNamespace(_cn=cn), body, R, owner)


def _counts(cn):
    return (scalar(cn, "SELECT COUNT(*) FROM mail_to"), scalar(cn, "SELECT COUNT(*) FROM watcher"))


@pytest.fixture(scope="module")
def room(cn):
    seed_names(cn, (R, "roster"), ("rf_a", "desk"), ("rf_b", "desk"), ("rf_c", "desk"))
    m1 = int(rec_mail.insert(cn, R, "rf_a", "rf_b", "root")[0]["id"])
    m2 = int(rec_mail.insert(cn, R, "rf_b", "rf_a", "child")[0]["id"])
    rec_tree.create(cn, "rf270room", "mail", m1)
    rec_tree.add(cn, "mail", m1, "mail", m2, "rf270room")
    return {"m1": m1, "m2": m2}


def _plain(msg: str) -> None:
    assert "\n" not in msg
    assert "1644" not in msg and "45000" not in msg and not msg.startswith("(")


def test_remove_not_a_recipient_is_one_plain_line(cn, room):
    before = _counts(cn)
    with pytest.raises(CoordError) as ei:
        _go(cn, "remove", "mail", room["m2"], "rf_c")
    assert str(ei.value) == "remove: not a recipient on this letter or under it"
    _plain(str(ei.value))
    assert _counts(cn) == before


def test_remove_orphan_is_one_plain_line(cn, room):
    before = _counts(cn)
    with pytest.raises(CoordError) as ei:
        _go(cn, "remove", "mail", room["m2"], "rf_a")
    assert str(ei.value) == f"remove: mail {room['m2']} would have no recipient"
    _plain(str(ei.value))
    assert _counts(cn) == before


@pytest.mark.parametrize("fn", ["put", "delete", "set_hint"])
def test_watcher_on_mail_refused_by_name(cn, room, fn):
    before = _counts(cn)
    did = scalar(cn, "SELECT id FROM name WHERE type='desk' AND name='rf_c'")
    args = (cn, "mail", room["m1"], did) + (("x",) if fn == "set_hint" else ())
    with pytest.raises(CoordError) as ei:
        getattr(rec_w, fn)(*args)
    assert str(ei.value) == rec_w.NOT_ON_MAIL
    _plain(str(ei.value))
    assert _counts(cn) == before


def test_watcher_on_mail_upper_case_type_refused(cn, room):
    with pytest.raises(CoordError, match="watchers do not watch mail"):
        rec_w.put(cn, "MAIL", room["m1"], 1)
