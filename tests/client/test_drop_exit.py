"""Refused mill drop exits 1 (Validator 0.6.25 #126 warning)."""
from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from agent_coord.client import http


@pytest.mark.parametrize(
    "result,rc",
    [
        ({"released": False, "reason": "not held by you", "owner": None}, 1),
        ({"released": True, "was_owner": "me", "owner": None}, 0),
    ],
)
def test_drop_exit_code(result, rc, capsys):
    reply = {"ok": True, "result": result}
    with patch.object(http, "mill_http_call", return_value=reply), patch(
        "agent_coord.client.outbound.body_from_args", return_value={"verb": "drop"}
    ):
        assert http.mill_http_from_args(SimpleNamespace(cmd="drop")) == rc
    assert "released" in capsys.readouterr().out


def test_refused_drop_top_level_ok_is_false(capsys):
    reply = {
        "ok": True,
        "result": {
            "ok": False,
            "released": False,
            "owner": "builder",
            "reason": "held by builder, not you",
        },
    }
    with patch.object(http, "mill_http_call", return_value=reply), patch(
        "agent_coord.client.outbound.body_from_args", return_value={"verb": "drop"}
    ):
        rc = http.mill_http_from_args(SimpleNamespace(cmd="drop"))
    captured = capsys.readouterr()
    assert rc == 1
    assert captured.err == ""
    out = json.loads(captured.out)
    assert out["ok"] is False
    assert out["result"]["ok"] is False
    assert out["result"]["released"] is False
    captured.out.encode("ascii")


def test_raw_refused_drop_also_exits_1():
    reply = {"ok": True, "result": {"released": False, "reason": "not held by you"}}
    with patch.object(http, "mill_http_call", return_value=reply), patch(
        "agent_coord.client.outbound.body_from_args", return_value={"verb": "drop"}
    ):
        assert http.mill_http_from_args(SimpleNamespace(cmd="drop", raw=True)) == 1


def test_other_verbs_unchanged():
    reply = {"ok": True, "result": {"released": False}}
    with patch.object(http, "mill_http_call", return_value=reply), patch(
        "agent_coord.client.outbound.body_from_args", return_value={"verb": "hold"}
    ):
        assert http.mill_http_from_args(SimpleNamespace(cmd="hold")) == 0
