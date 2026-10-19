"""claim sends --eta and --msg, and no longer advertises --lease (#232)."""
from __future__ import annotations

import os
import subprocess
import sys
from types import SimpleNamespace

from agent_coord.client.outbound import body_from_args
from agent_coord.client.ws import write_rpc_bridge


def _sitting(monkeypatch, tmp_path, desk: str) -> None:
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    monkeypatch.delenv("AGENT_COORD_OWNER", raising=False)
    write_rpc_bridge(desk, port=9, secret="sitting", pid=os.getpid())


def test_claim_body_sends_eta_and_msg(monkeypatch, tmp_path) -> None:
    _sitting(monkeypatch, tmp_path, "build-ui")
    body = body_from_args(
        SimpleNamespace(
            cmd="claim",
            project="the-mill",
            need="card-232",
            eta="2h",
            msg="hi",
        )
    )
    assert body["verb"] == "claim"
    assert body["need"] == "card-232"
    assert body["eta"] == "2h"
    assert body["msg"] == "hi"
    assert "lease" not in body


def test_claim_help_lists_eta_and_msg_only() -> None:
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    env = os.environ.copy()
    env["PYTHONPATH"] = root
    got = subprocess.run(
        [sys.executable, "-m", "agent_coord", "claim", "-h"],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
    )
    assert got.returncode == 0
    text = got.stdout
    assert "--eta" in text
    assert "--msg" in text
    assert "--lease" not in text
