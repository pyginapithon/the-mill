"""Regression row F34 (db-driver-c). No live SQL.

The book runs on the connector's C extension by default. Pure Python is only a
fallback: one warning line in the server log, db_driver in /health and in the
mill-perf startup line. On the OpenSSL clash (bundled OpenSSL 3.2+ vs a system
OpenSSL 3.0 already loaded by ssl) the Wall restarts once with the bundled
libraries preloaded.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

from agent_coord.server.records import driver

CLASH = (
    "ImportError: /lib/x86_64-linux-gnu/libssl.so.3: version `OPENSSL_3.2.0' not found "
    "(required by /x/site-packages/_mysql_connector.cpython-312-x86_64-linux-gnu.so)"
)
LIBS = ["/x/mysql/vendor/libssl.so.3", "/x/mysql/vendor/libcrypto.so.3"]


def test_clash_is_only_the_openssl_symbol_error() -> None:
    assert driver.openssl_clash(CLASH)
    assert not driver.openssl_clash("ModuleNotFoundError: No module named '_mysql_connector'")
    assert not driver.openssl_clash("")


def test_reexec_plan_preloads_bundled_openssl_once() -> None:
    env = driver.reexec_plan(CLASH, platform="linux", environ={"PATH": "/bin"}, libs=LIBS)
    assert env is not None
    assert env["LD_PRELOAD"] == ":".join(LIBS)
    assert env[driver.REEXEC_ENV] == "1"
    assert env[driver.PREV_PRELOAD_ENV] == ""
    assert env["PATH"] == "/bin"
    # second pass never restarts again
    assert driver.reexec_plan(CLASH, platform="linux", environ=env, libs=LIBS) is None


def test_reexec_plan_passes_the_system_ca() -> None:
    env = driver.reexec_plan(CLASH, platform="linux", environ={}, libs=LIBS, ca_file="/etc/ssl/ca.pem", ca_dir="/etc/ssl/certs")
    assert env["SSL_CERT_FILE"] == "/etc/ssl/ca.pem"
    assert env["SSL_CERT_DIR"] == "/etc/ssl/certs"
    own = driver.reexec_plan(CLASH, platform="linux", environ={"SSL_CERT_FILE": "/office/ca.pem"}, libs=LIBS, ca_file="/etc/ssl/ca.pem")
    assert own["SSL_CERT_FILE"] == "/office/ca.pem"
    bare = driver.reexec_plan(CLASH, platform="linux", environ={}, libs=LIBS)
    assert "SSL_CERT_FILE" not in bare and "SSL_CERT_DIR" not in bare


def test_reexec_plan_keeps_an_existing_preload() -> None:
    env = driver.reexec_plan(CLASH, platform="linux", environ={"LD_PRELOAD": "/opt/a.so"}, libs=LIBS)
    assert env["LD_PRELOAD"] == ":".join(LIBS + ["/opt/a.so"])
    assert env[driver.PREV_PRELOAD_ENV] == "/opt/a.so"


@pytest.mark.parametrize(
    "err,platform,libs",
    [
        (CLASH, "darwin", LIBS),  # macOS wheels use two-level names; no clash
        (CLASH, "win32", LIBS),
        ("ModuleNotFoundError: No module named '_mysql_connector'", "linux", LIBS),  # pure wheel
        ("", "linux", LIBS),  # C ext loaded fine
        (CLASH, "linux", []),  # no bundled OpenSSL to preload
    ],
)
def test_reexec_plan_none(err, platform, libs) -> None:
    assert driver.reexec_plan(err, platform=platform, environ={}, libs=libs) is None


def test_after_restart_the_preload_is_put_back(monkeypatch) -> None:
    monkeypatch.setenv(driver.REEXEC_ENV, "1")
    monkeypatch.setenv(driver.PREV_PRELOAD_ENV, "/opt/a.so")
    monkeypatch.setenv("LD_PRELOAD", ":".join(LIBS + ["/opt/a.so"]))
    driver.ensure_c_path()
    assert os.environ["LD_PRELOAD"] == "/opt/a.so"
    assert driver.PREV_PRELOAD_ENV not in os.environ
    monkeypatch.setenv(driver.PREV_PRELOAD_ENV, "")
    driver.ensure_c_path()
    assert "LD_PRELOAD" not in os.environ


def test_forced_pure_never_restarts(monkeypatch) -> None:
    monkeypatch.delenv(driver.REEXEC_ENV, raising=False)
    monkeypatch.setattr(driver, "forced_pure", lambda: True)
    monkeypatch.setattr(driver.os, "execve", lambda *a: pytest.fail("restarted under use_pure"))
    driver.ensure_c_path()


def test_clash_restarts_the_same_command(monkeypatch) -> None:
    seen = {}
    monkeypatch.delenv(driver.REEXEC_ENV, raising=False)
    monkeypatch.setattr(driver, "forced_pure", lambda: False)
    monkeypatch.setattr(driver, "cext_error", lambda: CLASH)
    monkeypatch.setattr(driver, "vendor_openssl", lambda: LIBS)
    monkeypatch.setattr(driver.sys, "platform", "linux")
    monkeypatch.setattr(driver.sys, "orig_argv", ["/usr/bin/python3", "-m", "agent_coord", "wall", "--port", "443"], raising=False)
    monkeypatch.setattr(driver.os, "execve", lambda exe, argv, env: seen.update(exe=exe, argv=argv, env=env))
    driver.ensure_c_path()
    assert seen["argv"][1:] == ["-m", "agent_coord", "wall", "--port", "443"]
    assert seen["env"]["LD_PRELOAD"].startswith(LIBS[0])


def test_fallback_warning_once(monkeypatch, capsys) -> None:
    monkeypatch.setattr(driver, "_WARNED", type(driver._WARNED)())
    pure = {"path": "pure", "reason": CLASH, "version": "26.7.0"}
    driver.warn_once(pure)
    driver.warn_once(pure)
    err = capsys.readouterr().err.splitlines()
    assert len(err) == 1
    assert err[0].startswith("mill: WARNING MySQL driver is pure Python (")
    assert "OPENSSL_3.2.0" in err[0]
    assert "--only-binary=:all:" in err[0]
    assert err[0].isascii()
    driver.warn_once({"path": "c"})
    assert capsys.readouterr().err == ""


def test_active_reports_use_pure(monkeypatch) -> None:
    monkeypatch.setattr(driver, "forced_pure", lambda: True)
    info = driver.active()
    assert info["path"] == "pure"
    assert info["reason"] == "use_pure is set"
    assert "unset use_pure" in driver.fallback_line(info)


def test_startup_perf_line_names_the_driver(monkeypatch) -> None:
    from agent_coord.server import asgi, push

    lines = []
    monkeypatch.setattr(push, "perf_log", lambda op, ms, **kv: lines.append((op, kv)))
    monkeypatch.setattr(driver, "cached", lambda: {"path": "c", "version": "26.7.0", "reason": ""})
    asgi.log_startup()
    assert lines and lines[0][0] == "startup"
    assert lines[0][1]["db_driver"] == "c"
    assert lines[0][1]["connector"] == "26.7.0"


def test_driver_check_cli_runs_after_the_wall_startup() -> None:
    """The CI gate command. Requires the C path only where the wheel ships one."""
    pytest.importorskip("mysql.connector")
    import importlib.util

    if importlib.util.find_spec("_mysql_connector") is None:
        pytest.skip("pure connector wheel on this platform")
    env = {k: v for k, v in os.environ.items() if k not in ("AGENT_COORD_USE_PURE",)}
    r = subprocess.run(
        [sys.executable, "-m", "agent_coord.server.records.driver", "--require-c"],
        capture_output=True, text=True, timeout=60, env=env,
    )
    assert r.returncode == 0, r.stderr
    info = json.loads(r.stdout.strip().splitlines()[-1])
    assert info["path"] == "c"
