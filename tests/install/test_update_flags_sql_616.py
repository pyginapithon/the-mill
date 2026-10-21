"""#616 without MySQL: mill update never applies book SQL. It checks the stamp with
the new pack, flags stale SQL with the apply command, and still starts the wall.
Row F66 (sql-stamp)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from agent_coord.install import migrate, run_update
from agent_coord.install.host import sql_install_cmd

FIX = "mill install sql --apply"


class Proc:
    def __init__(self, code: int = 0, err: str = "", out: str = "") -> None:
        self.returncode = code
        self.stderr = err
        self.stdout = out


def _update(tmp_path, sql_proc: Proc):
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
        if list(cmd[:5]) == sql_install_cmd(apply=False)[:5]:
            return sql_proc
        return Proc()

    row = run_update(
        apply=True, cwd=tmp_path, dest=tmp_path, run_cmd=runner, private_ips=["203.0.113.9"],
        already_admin=True, stop_poll_s=0, connect_pids=_no_connect,
    )
    return row, seen, _is_import_check, _is_wall_start


def _state(ok: bool) -> str:
    book = "aaaaaaaaaaaa" if ok else "bbbbbbbbbbbb"
    return json.dumps({"ok": ok, "pack": "aaaaaaaaaaaa", "book": book, "fix": FIX, "applied": False})


def test_update_never_applies_sql(tmp_path):
    for proc in (Proc(0, out=_state(True)), Proc(1, out=_state(False)), Proc(1, err="book down")):
        _row, seen, _imp, _start = _update(tmp_path, proc)
        assert not any("--apply" in c for c in seen), seen


def test_update_checks_sql_after_import_before_start(tmp_path):
    row, seen, is_import, is_start = _update(tmp_path, Proc(0, out=_state(True)))
    assert row["ok"] is True and row["schema"] == "current"
    imp = next(i for i, c in enumerate(seen) if is_import(c))
    sql = seen.index(sql_install_cmd(apply=False))
    start = next(i for i, c in enumerate(seen) if is_start(c))
    assert imp < sql < start


def test_update_flags_stale_sql_and_still_starts_the_wall(tmp_path):
    row, seen, _imp, is_start = _update(tmp_path, Proc(1, out=_state(False)))
    assert row["schema"] == "stale"
    assert row["ok"] is False  # mill update exits 1
    assert row["pip_applied"] is True
    assert row["wall_restart"] == "ok" and any(is_start(c) for c in seen)
    assert row["sql"] == {"book": "bbbbbbbbbbbb", "pack": "aaaaaaaaaaaa"}
    assert FIX in row["error"]
    text = " ".join(row["next"]).lower()
    assert FIX in text and "back up the book" in text and "a/b" in text


def test_update_names_the_check_when_it_cannot_read_the_book(tmp_path):
    row, seen, _imp, is_start = _update(tmp_path, Proc(1, err="book down"))
    assert row["schema"] == "unchecked" and row["ok"] is False
    assert "book down" in row["error"] and "mill install sql" in row["error"]
    assert any(is_start(c) for c in seen)


def test_sql_install_cmd_is_the_installed_pack():
    base = [sys.executable or "python", "-m", "agent_coord", "install", "sql"]
    assert sql_install_cmd(apply=False) == base
    assert sql_install_cmd(apply=True) == base + ["--apply"]


def test_install_sql_apply_runs_the_one_migration_entry(monkeypatch):
    calls = []
    states = iter([{"ok": False, "book": "", "pack": "p", "fix": FIX}, {"ok": True, "book": "p", "pack": "p", "fix": FIX}])
    monkeypatch.setattr(migrate, "sql_state", lambda cn: next(states))
    monkeypatch.setattr(migrate, "ensure", lambda cn: calls.append(cn) or {"applied": ["a", "b"]})
    row = migrate.install_sql("cn", apply=True)
    assert calls == ["cn"] and row["ok"] is True and row["applied"] is True and row["steps"] == 2


def test_install_sql_without_apply_only_reports(monkeypatch):
    monkeypatch.setattr(migrate, "sql_state", lambda cn: {"ok": False, "book": "", "pack": "p", "fix": FIX})
    monkeypatch.setattr(migrate, "ensure", lambda cn: (_ for _ in ()).throw(AssertionError("applied")))
    assert migrate.install_sql("cn", apply=False)["applied"] is False
