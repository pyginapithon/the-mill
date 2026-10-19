# -*- coding: utf-8 -*-
from agent_coord.client.watch_filter import load_want, save_want, wants


def test_empty_accepts_all(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("agent_coord.config.mill_home", lambda: tmp_path)
    assert wants("builder", {"type": "mail", "hint": "MAIL", "route": "mail:MAIL"})
    assert wants("builder", {"type": "name", "hint": "NAME", "route": "name:NAME"})


def test_allowlist(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("agent_coord.config.mill_home", lambda: tmp_path)
    save_want("builder", {"mail:MAIL": ""})
    assert wants("builder", {"type": "mail", "hint": "MAIL", "route": "mail:MAIL"})
    assert not wants("builder", {"type": "todo", "hint": "TODO", "route": "todo:TODO"})


def test_star(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("agent_coord.config.mill_home", lambda: tmp_path)
    save_want("builder", {"*": ""})
    assert wants("builder", {"type": "score", "hint": "SCORE", "route": "score:SCORE"})


def test_ping_false(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("agent_coord.config.mill_home", lambda: tmp_path)
    save_want("builder", {"*": ""})
    assert not wants("builder", {"hint": "PING"})


def test_roundtrip(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("agent_coord.config.mill_home", lambda: tmp_path)
    save_want("builder", {"mail:MAIL": "", "todo:TODO": ""})
    assert set(load_want("builder")) == {"mail:MAIL", "todo:TODO"}
