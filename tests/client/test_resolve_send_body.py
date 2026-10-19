"""#483 mill send @file / stdin body expansion."""
from __future__ import annotations


import pytest


from agent_coord.client.outbound import body_from_args, resolve_send_body
from agent_coord.helpers.errors import CoordError


def test_resolve_inline():
    assert resolve_send_body("hello world") == "hello world"


def test_resolve_at_file(tmp_path):
    f = tmp_path / "letter.txt"
    f.write_text("from file\nsecond", encoding="utf-8")
    got = resolve_send_body("@" + str(f))
    assert "from file" in got and "second" in got


def test_resolve_at_missing(tmp_path):
    with pytest.raises(CoordError, match="not found"):
        resolve_send_body("@" + str(tmp_path / "nope.txt"))


def test_resolve_dash_tty(monkeypatch):
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    with pytest.raises(CoordError, match="stdin"):
        resolve_send_body("-")


def test_resolve_dash_pipe(monkeypatch):
    class S:
        def isatty(self):
            return False

        def read(self):
            return "piped body"

    monkeypatch.setattr("sys.stdin", S())
    assert resolve_send_body("-") == "piped body"

