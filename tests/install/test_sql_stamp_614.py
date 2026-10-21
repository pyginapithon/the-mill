"""#614 without MySQL: the pack digest and health on stale SQL. Row F66 (sql-stamp). mill update: #616."""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

from agent_coord.install import migrate

FIX = "mill install sql --apply"


def _copy_sql(tmp_path: Path, monkeypatch) -> Path:
    dst = tmp_path / "sql"
    shutil.copytree(migrate.sql_dir(), dst)
    monkeypatch.setattr(migrate, "sql_dir", lambda: dst)
    migrate.sql_digest.cache_clear()
    return dst


def test_digest_changes_when_a_procedure_file_changes(tmp_path, monkeypatch):
    before = migrate.sql_digest()
    dst = _copy_sql(tmp_path, monkeypatch)
    assert migrate.sql_digest() == before
    sp = dst / "sp_name.sql"
    sp.write_text(sp.read_text(encoding="utf-8") + "\n-- changed\n", encoding="utf-8")
    migrate.sql_digest.cache_clear()
    assert migrate.sql_digest() != before
    migrate.sql_digest.cache_clear()


def test_digest_ignores_line_endings(tmp_path, monkeypatch):
    before = migrate.sql_digest()
    dst = _copy_sql(tmp_path, monkeypatch)
    for p in dst.glob("*.sql"):
        p.write_bytes(p.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    migrate.sql_digest.cache_clear()
    assert migrate.sql_digest() == before
    migrate.sql_digest.cache_clear()


def _health(monkeypatch, state):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
    from test_book_health import _Fake, _bind

    from agent_coord.server.middleware import make_handler
    from agent_coord.server.records import db

    monkeypatch.setattr(db, "book_ping", lambda: True)
    monkeypatch.setattr(db, "book_sql_state", lambda: state)
    handler = make_handler({}, api_only=True)
    hit = _Fake("/health")
    _bind(handler, hit)
    hit.do_GET()
    return hit._code, json.loads(hit._body.decode("ascii"))


def test_health_is_503_naming_the_fix_when_the_sql_is_stale(monkeypatch):
    code, body = _health(monkeypatch, {"ok": False, "pack": "aaaaaaaaaaaa", "book": "bbbbbbbbbbbb", "fix": FIX})
    assert code == 503
    assert body == {
        "ok": False,
        "error": "book SQL is not this pack's (book bbbbbbbbbbbb, pack aaaaaaaaaaaa)",
        "fix": FIX,
    }


def test_health_is_200_when_the_sql_matches(monkeypatch):
    code, body = _health(monkeypatch, {"ok": True, "pack": "aaaaaaaaaaaa", "book": "aaaaaaaaaaaa", "fix": FIX})
    assert code == 200 and body["ok"] is True
