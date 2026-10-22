"""#656: mill_mail_update / mill_mail_delete act only for the letter's sender or an Admin desk."""
from __future__ import annotations

import mysql.connector
import pytest

pytestmark = pytest.mark.sql

from agent_coord.server.records import mail
from agent_coord.server.records.db import scalar
from tests.server.records.conftest import seed_names

REFUSED = "only the sender or an Admin desk"


def _letter(cn, body: str) -> int:
    seed_names(cn, ("ms_proj", "roster"), ("ms_from", "desk"), ("ms_to", "desk"), ("ms_other", "desk"), ("ms_admin", "desk"))
    return int(mail.insert(cn, "ms_proj", "ms_from", "ms_to", body)[0]["id"])


def _make_admin(cn, desk: str) -> None:
    did = int(scalar(cn, "SELECT id FROM name WHERE type='desk' AND name=%s", (desk,)))
    aid = 2  # the reserved Admin roster id (#722)
    cur = cn.cursor()
    cur.execute("INSERT IGNORE INTO member (name_id, desk_id) VALUES (%s, %s)", (aid, did))
    cur.close()
    cn.commit()


def _body(cn, mid: int):
    return scalar(cn, "SELECT body FROM mail WHERE id=%s", (mid,))


@pytest.mark.parametrize("caller", ["ms_other", "ms_to", "ms_nobody"])
def test_non_sender_update_changes_nothing(cn, caller) -> None:
    mid = _letter(cn, "original")
    with pytest.raises(mysql.connector.Error) as ei:
        mail.update(cn, mid, caller, body="rewritten")
    assert REFUSED in str(ei.value)
    assert _body(cn, mid) == "original"


@pytest.mark.parametrize("caller", ["ms_other", "ms_to", "ms_nobody"])
def test_non_sender_delete_leaves_the_row(cn, caller) -> None:
    mid = _letter(cn, "keep me")
    with pytest.raises(mysql.connector.Error) as ei:
        mail.delete(cn, mid, caller)
    assert REFUSED in str(ei.value)
    assert _body(cn, mid) == "keep me"
    assert scalar(cn, "SELECT COUNT(*) FROM mail_to WHERE type='mail' AND id=%s", (mid,)) >= 1
    assert scalar(cn, "SELECT deleted FROM activity WHERE type='mail' AND id=%s", (mid,)) is None


def test_sender_can_update_and_delete(cn) -> None:
    mid = _letter(cn, "one")
    mail.update(cn, mid, "ms_from", body="two")
    assert _body(cn, mid) == "two"
    mail.delete(cn, mid, "ms_from")
    assert _body(cn, mid) is None


def test_admin_can_update_and_delete(cn) -> None:
    mid = _letter(cn, "one")
    _make_admin(cn, "ms_admin")
    mail.update(cn, mid, "ms_admin", body="by admin")
    assert _body(cn, mid) == "by admin"
    mail.delete(cn, mid, "ms_admin")
    assert _body(cn, mid) is None


def test_update_of_missing_letter_is_refused(cn) -> None:
    with pytest.raises(mysql.connector.Error) as ei:
        mail.update(cn, 987654321, "ms_from", body="x")
    assert "no such letter" in str(ei.value)
