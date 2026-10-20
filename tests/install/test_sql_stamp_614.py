"""#614 without MySQL: the pack digest, health on stale SQL, and mill update runs the SQL step. Row F66 (sql-stamp)."""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

from agent_coord.install import migrate, run_update
from agent_coord.install.host import sql_install_cmd

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


class Proc:
    def __init__(self, code: int = 0, err: str = "", out: str = "") -> None:
        self.returncode = code
        self.stderr = err
        self.stdout = out


def _update(tmp_path, sql_code: int):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from test_mill_update import _is_import_check, _is_wall_query, _is_wall_start, _is_wall_stop, _no_connect, _query_text

    seen: list[list[str]] = []
    phase = {"stopped": False}

    def runner(cmd, **kwargs):
        seen.append(list(cmd))
        if _is_wall_query(cmd):
            return Proc(out=_query_text(running=not phase["stopped"]))
        if _is_wall_stop(cmd):
            phase["stopped"] = True
        if list(cmd) == sql_install_cmd():
            return Proc(sql_code, "ensure failed" if sql_code else "")
        return Proc()

    row = run_update(
        apply=True, cwd=tmp_path, dest=tmp_path, run_cmd=runner, private_ips=["203.0.113.9"],
        already_admin=True, stop_poll_s=0, connect_pids=_no_connect,
    )
    return row, seen, _is_import_check, _is_wall_start


def test_update_applies_the_sql_after_import_before_start(tmp_path):
    row, seen, is_import, is_start = _update(tmp_path, 0)
    assert row["ok"] is True and row["schema"] == "applied"
    imp = next(i for i, c in enumerate(seen) if is_import(c))
    sql = seen.index(sql_install_cmd())
    start = next(i for i, c in enumerate(seen) if is_start(c))
    assert imp < sql < start


def test_update_sql_failure_does_not_start_the_wall(tmp_path):
    row, seen, _imp, is_start = _update(tmp_path, 1)
    assert row["ok"] is False and row["schema"] == "failed"
    assert row["wall_restart"] == "skipped"
    assert "ensure failed" in row["error"] and FIX in row["error"]
    assert not any(is_start(c) for c in seen)


def test_sql_install_cmd_is_the_installed_pack():
    assert sql_install_cmd() == [sys.executable or "python", "-m", "agent_coord", "install", "sql", "--apply"]
