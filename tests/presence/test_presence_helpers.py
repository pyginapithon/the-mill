"""protocol/presence tokens + vendor (session glue; keep)."""
from __future__ import annotations

import hashlib

import pytest

from agent_coord.client.vendor import session_vendor
from agent_coord.client.tokens import token_hash
from agent_coord.client.tokens import token_hash as hash_mod
from agent_coord.client.vendor import session_vendor as vendor_mod


def test_session_vendor_env(monkeypatch):
    monkeypatch.setenv("AGENT_COORD_VENDOR", "Grok")
    assert session_vendor() == "grok"
    assert vendor_mod() == "grok"
    monkeypatch.setenv("AGENT_COORD_VENDOR", "x" * 40)
    assert len(session_vendor()) == 32
    monkeypatch.delenv("AGENT_COORD_VENDOR", raising=False)
    assert session_vendor() == ""


@pytest.mark.parametrize(
    "token",
    ["abc", "", "token-with-unicode-v", "a" * 64],
)
def test_token_hash_sha256(token):
    expect = hashlib.sha256(token.encode("utf-8")).hexdigest()
    assert token_hash(token) == expect
    assert hash_mod(token) == expect
