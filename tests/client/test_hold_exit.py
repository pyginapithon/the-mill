"""A refused hold exits 1 and names the holder on stdout, like drop (#142, #193)."""
from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import patch

from agent_coord.client import http


def test_refused_hold_exits_1_on_stdout(capsys):
    reply = {
        "ok": True,
        "result": {"ok": False, "held": False, "owner": "builder", "resource": "agent_coord/client/ws.py"},
        "sync": [],
    }
    with patch.object(http, "mill_http_call", return_value=reply), patch(
        "agent_coord.client.outbound.body_from_args", return_value={"verb": "hold"}
    ):
        rc = http.mill_http_from_args(SimpleNamespace(cmd="hold"))
    captured = capsys.readouterr()
    assert rc == 1
    assert captured.err == ""
    out = json.loads(captured.out)
    assert out["ok"] is False
    assert out["result"]["held"] is False
    assert out["result"]["reason"] == "held by builder, not you"
    captured.out.encode("ascii")


def test_peek_free_exits_0(capsys):
    reply = {
        "ok": True,
        "result": {
            "ok": True,
            "peek": True,
            "held": False,
            "owner": None,
            "resource": "f16-missing.res",
            "id": None,
            "since": None,
        },
        "sync": [],
    }
    args = SimpleNamespace(cmd="hold", peek=True)
    with patch.object(http, "mill_http_call", return_value=reply), patch(
        "agent_coord.client.outbound.body_from_args", return_value={"verb": "hold", "peek": True}
    ):
        rc = http.mill_http_from_args(args)
    captured = capsys.readouterr()
    assert rc == 0
    assert captured.err == ""
    out = json.loads(captured.out)
    assert out["ok"] is True
    assert out["result"]["peek"] is True
    assert out["result"]["held"] is False
    assert "reason" not in out["result"]
    captured.out.encode("ascii")
    row = {"ok": True, "result": {"ok": True, "peek": True, "held": False, "owner": None}}
    assert http._refused_hold(SimpleNamespace(cmd="hold"), row) is False
    bare = {"ok": True, "result": {"held": False}}
    assert http._refused_hold(SimpleNamespace(cmd="hold", peek=True), bare) is False


def test_taken_hold_stays_stdout_exit_0(capsys):
    reply = {"ok": True, "result": {"ok": True, "held": True, "owner": "grok-tui"}, "sync": []}
    with patch.object(http, "mill_http_call", return_value=reply), patch(
        "agent_coord.client.outbound.body_from_args", return_value={"verb": "hold"}
    ):
        rc = http.mill_http_from_args(SimpleNamespace(cmd="hold"))
    captured = capsys.readouterr()
    assert rc == 0
    assert captured.err == ""
    assert json.loads(captured.out)["result"]["held"] is True
