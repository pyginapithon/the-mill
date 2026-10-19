# -*- coding: utf-8 -*-
from agent_coord.client.ws import mill_ws_url


def test_mill_ws_url_http(monkeypatch) -> None:
    monkeypatch.setattr("agent_coord.client.http.mill_url", lambda: "http://127.0.0.1:8765")
    u = mill_ws_url("build-ui")
    assert u.startswith("ws://")
    assert u.endswith("/ws/build-ui")


def test_mill_ws_url_https(monkeypatch) -> None:
    monkeypatch.setattr("agent_coord.client.http.mill_url", lambda: "https://198.51.100.10")
    u = mill_ws_url("alice")
    assert u.startswith("wss://")
    assert "/ws/alice" in u
