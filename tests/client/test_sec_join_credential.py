# -*- coding: utf-8 -*-
"""Security: a cold seat join presents its seat credential (#sec S-2).

The gated office door now authorizes join. For a cold desk with no stored
session token, the seat from the welcome link (passed by offices.join_office in
the body `token`) must be sent so the door can authorize it in one command. An
open (path) office sends no credential.
"""
from __future__ import annotations

import json

import pytest

from agent_coord.client.http import mill_http_call


class _Resp:
    def __init__(self, payload: bytes):
        self._p = payload

    def read(self):
        return self._p

    headers = {"X-Mill-Version": "0"}

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


@pytest.fixture
def capture(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENT_COORD_MILL_URL", "https://office.example")
    monkeypatch.setenv("AGENT_COORD_MILL_HOME", str(tmp_path))
    monkeypatch.delenv("AGENT_COORD_TOKEN", raising=False)
    cap: dict = {}

    def fake_urlopen(req, context=None, timeout=None):
        cap["auth"] = req.headers.get("Authorization") or req.get_header("Authorization")
        cap["body"] = json.loads(req.data.decode("utf-8"))
        return _Resp(b'{"ok":true,"token":"new-sess","owner":"coldagent"}')

    monkeypatch.setattr(
        "agent_coord.client.http._open", fake_urlopen
    )
    return cap


def test_cold_join_sends_seat_as_bearer(capture):
    # No stored session token for this owner; the seat arrives in the body.
    row = mill_http_call(
        {
            "verb": "join",
            "project": "the-mill",
            "owner": "coldagent",
            "token": "seat-xyz",
        }
    )
    assert row["ok"] is True
    assert capture["auth"] == "Bearer seat-xyz"
    assert capture["body"].get("token") == "seat-xyz"


def test_open_path_join_sends_no_credential(capture):
    row = mill_http_call(
        {"verb": "join", "project": "the-mill", "owner": "coldagent"}
    )
    assert row["ok"] is True
    assert capture["auth"] is None
    assert "token" not in capture["body"]
