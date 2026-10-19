"""helpers/ident.py ident/file_key/this_host + coord CoordError."""
from __future__ import annotations

import pytest

from agent_coord import CoordError, LockHeld, default_owner, file_key, slug, this_host
from agent_coord.helpers.owner import holder_gone
from agent_coord.helpers.ident import _IDENT
from agent_coord.helpers.ident import file_key as file_key_rec
from agent_coord.helpers.ident import ident
from agent_coord.helpers.ident import this_host as host_rec


def test_slug_ok():
    assert slug("desk-1") == "desk-1"
    assert ident("desk-1") == "desk-1"


def test_slug_bad():
    with pytest.raises(CoordError):
        slug("no spaces")


def test_file_key_relative(tmp_path):
    p = tmp_path / "a.py"
    p.write_text("x", encoding="utf-8")
    k = file_key(p, project_root=tmp_path)
    assert "a.py" in k
    assert file_key_rec(p, project_root=tmp_path) == k


def test_this_host():
    assert this_host()
    assert host_rec() == this_host()


def test_default_owner(monkeypatch):
    monkeypatch.setenv("AGENT_COORD_OWNER", "build-skills")
    assert default_owner() == "build-skills"


def test_lockheld_is_hold():
    err = LockHeld("RES_x", {"owner": "d"})
    assert "RES_x" in str(err)


def test_holder_gone_no_book_pid():
    assert holder_gone(None, None) is False


def test_slug_regex():
    assert _IDENT.match("abc")
