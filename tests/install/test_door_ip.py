# -*- coding: utf-8 -*-
from agent_coord.server.admin.door import mode
from agent_coord.server.allow import allowed


def test_door_ip_mode(monkeypatch) -> None:
    monkeypatch.setenv("AGENT_COORD_DOOR", "ip")
    assert mode() == "ip"
    monkeypatch.setenv("AGENT_COORD_DOOR", "lan")
    assert mode() == "ip"


def test_door_ip_empty_rules_loopback_only() -> None:
    assert allowed("127.0.0.1", [], empty_open=False)
    assert not allowed("203.0.113.10", [], empty_open=False)
    assert allowed("203.0.113.10", ["203.0.113.0/24"], empty_open=False)
