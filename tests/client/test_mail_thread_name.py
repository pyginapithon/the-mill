"""mail-thread room names longer than 64 refuse before the wall (#208)."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from agent_coord.client.outbound import body_from_args
from agent_coord.helpers.errors import CoordError


def test_room_name_over_64_refuses():
    args = SimpleNamespace(cmd="mail-thread", mail_id="n" * 65, project="the-mill")
    with pytest.raises(CoordError) as ei:
        body_from_args(args)
    msg = str(ei.value)
    assert msg.startswith("mail-thread: no mail room named")
    assert len(msg.split("named", 1)[1].strip()) == 64


def test_room_name_of_64_is_sent_as_tree():
    name = "e" * 64
    args = SimpleNamespace(cmd="mail-thread", mail_id=name, project="the-mill")
    body = body_from_args(args)
    assert body["tree"] == name
