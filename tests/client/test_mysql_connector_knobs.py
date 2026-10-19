"""Connector knobs: omit unset; explicit env/config wins."""
from __future__ import annotations

from agent_coord.config import mysql_kwargs, mysql_cursor_kwargs, _as_bool


def test_as_bool_empty_uses_default() -> None:
    assert _as_bool("", default=False) is False
    assert _as_bool("", default=None) is None
    assert _as_bool(None, default=True) is True
    assert _as_bool("yes") is True
    assert _as_bool("off") is False


def test_mysql_kwargs_omit_when_unset(monkeypatch, tmp_path) -> None:
    cfg = tmp_path / "config.toml"
    cfg.write_text(
        "host = \"127.0.0.1\"\nport = 3306\nuser = \"u\"\npassword = \"p\"\ndatabase = \"d\"\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("AGENT_COORD_USE_PURE", raising=False)
    monkeypatch.delenv("AGENT_COORD_COMPRESS", raising=False)
    monkeypatch.delenv("AGENT_COORD_BUFFERED", raising=False)
    kw = mysql_kwargs(cfg)
    assert "use_pure" not in kw
    assert "compress" not in kw
    assert mysql_cursor_kwargs(cfg) == {}


def test_mysql_kwargs_env_override(monkeypatch, tmp_path) -> None:
    cfg = tmp_path / "config.toml"
    cfg.write_text(
        "host = \"127.0.0.1\"\nport = 3306\nuser = \"u\"\npassword = \"p\"\ndatabase = \"d\"\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("AGENT_COORD_USE_PURE", "1")
    monkeypatch.setenv("AGENT_COORD_COMPRESS", "true")
    monkeypatch.setenv("AGENT_COORD_BUFFERED", "yes")
    kw = mysql_kwargs(cfg)
    assert kw["use_pure"] is True
    assert kw["compress"] is True
    assert mysql_cursor_kwargs(cfg)["buffered"] is True
