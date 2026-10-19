"""Which MySQL driver path the book runs on: the connector's C extension or pure Python.

The C extension is the default. Pure Python is only the fallback, and the Wall
says so once in its log, in /health and in the mill-perf startup line (F34).

Linux wheels of mysql-connector-python bundle OpenSSL 3.2+ under mysql/vendor.
Python's own ssl module links the system OpenSSL. On a host whose OpenSSL is
older (Ubuntu 22.04/24.04, Debian 12: OpenSSL 3.0), whichever library loads
first wins the libssl.so.3 name, and the C extension then fails to import with
"version `OPENSSL_3.2.0' not found". The Wall fixes that by restarting itself
once with the bundled OpenSSL preloaded. OpenSSL 3.x keeps its ABI across minor
releases, so the ssl module runs on the newer bundled library unchanged.
"""

from __future__ import annotations

import importlib.util
import os
import sys
import threading
from pathlib import Path
from typing import Any

REEXEC_ENV = "MILL_DB_CEXT_REEXEC"
PREV_PRELOAD_ENV = "MILL_DB_PREV_LD_PRELOAD"
_WARNED = threading.Event()
_ACTIVE: dict[str, Any] = {}


def cext_error() -> str:
    """Empty when the C extension imports in this process, else the import error."""
    try:
        import _mysql_connector  # noqa: F401
    except Exception as exc:  # ImportError, OSError from the loader
        return f"{type(exc).__name__}: {exc}"
    return ""


def openssl_clash(err: str) -> bool:
    """The import failed on OpenSSL symbol versions, not on a missing module."""
    return "version `OPENSSL_" in (err or "") and "not found" in err


def vendor_openssl() -> list[str]:
    """The libssl/libcrypto that the connector wheel bundles, without importing it."""
    try:
        spec = importlib.util.find_spec("mysql")
    except Exception:
        return []
    for root in list(getattr(spec, "submodule_search_locations", None) or []):
        vendor = Path(root) / "vendor"
        libs = [vendor / "libssl.so.3", vendor / "libcrypto.so.3"]
        if all(p.is_file() for p in libs):
            return [str(p) for p in libs]
    return []


def forced_pure() -> bool:
    """use_pure / AGENT_COORD_USE_PURE set true by the office."""
    try:
        from agent_coord.config import mysql_kwargs

        return mysql_kwargs().get("use_pure") is True
    except Exception:
        return False


def reexec_plan(
    err: str,
    *,
    platform: str | None = None,
    environ: dict[str, str] | None = None,
    libs: list[str] | None = None,
    ca_file: str = "",
    ca_dir: str = "",
) -> dict[str, str] | None:
    """Environment for one restart with the bundled OpenSSL preloaded, or None.

    Only on Linux, only for the OpenSSL clash, only when the bundled libraries
    exist, and never twice (the marker stops a loop). The bundled OpenSSL was
    built with another default CA location, so the system CA file and dir are
    passed on as SSL_CERT_FILE / SSL_CERT_DIR unless the office set them.
    """
    env = dict(os.environ if environ is None else environ)
    if (platform or sys.platform) != "linux" or env.get(REEXEC_ENV):
        return None
    if not openssl_clash(err):
        return None
    libs = vendor_openssl() if libs is None else libs
    if not libs:
        return None
    prev = env.get("LD_PRELOAD", "")
    env[PREV_PRELOAD_ENV] = prev
    env["LD_PRELOAD"] = ":".join(libs + ([prev] if prev else []))
    env[REEXEC_ENV] = "1"
    if ca_file and not env.get("SSL_CERT_FILE"):
        env["SSL_CERT_FILE"] = ca_file
    if ca_dir and not env.get("SSL_CERT_DIR"):
        env["SSL_CERT_DIR"] = ca_dir
    return env


def system_ca() -> tuple[str, str]:
    """The CA file and dir of the OpenSSL that Python's ssl loaded (existing ones only)."""
    try:
        import ssl

        p = ssl.get_default_verify_paths()
    except Exception:
        return "", ""
    ca_file = p.openssl_cafile if p.openssl_cafile and os.path.isfile(p.openssl_cafile) else ""
    ca_dir = p.openssl_capath if p.openssl_capath and os.path.isdir(p.openssl_capath) else ""
    return ca_file, ca_dir


def ensure_c_path() -> None:
    """Call first in a long-lived server process, before it serves anything.

    Imports ssl the way the Wall will, then the C extension. On the OpenSSL
    clash, restarts this same command once with the bundled OpenSSL preloaded.
    After that restart, LD_PRELOAD is put back so child processes are unchanged.
    """
    if os.environ.get(REEXEC_ENV):
        prev = os.environ.pop(PREV_PRELOAD_ENV, "")
        if prev:
            os.environ["LD_PRELOAD"] = prev
        else:
            os.environ.pop("LD_PRELOAD", None)
        return
    if forced_pure():
        return
    import ssl  # noqa: F401  (load order the server has anyway)

    ca_file, ca_dir = system_ca()
    env = reexec_plan(cext_error(), ca_file=ca_file, ca_dir=ca_dir)
    if env is None:
        return
    argv = list(getattr(sys, "orig_argv", None) or [sys.executable, *sys.argv])
    sys.stdout.flush()
    sys.stderr.flush()
    os.execve(sys.executable, [sys.executable, *argv[1:]], env)


def active() -> dict[str, Any]:
    """The driver the book connections use. path is c or pure."""
    info: dict[str, Any] = {"driver": "mysql-connector-python", "version": "", "path": "pure", "reason": ""}
    try:
        import mysql.connector

        info["version"] = str(getattr(mysql.connector, "__version__", ""))
        have = bool(getattr(mysql.connector, "HAVE_CEXT", False))
    except Exception as exc:
        info["reason"] = f"{type(exc).__name__}: {exc}"
        return info
    if forced_pure():
        info["reason"] = "use_pure is set"
    elif have:
        info["path"] = "c"
    else:
        info["reason"] = cext_error() or "C extension not installed"
    return info


def cached() -> dict[str, Any]:
    """active() once per process (the driver cannot change after import)."""
    if not _ACTIVE:
        _ACTIVE.update(active())
    return dict(_ACTIVE)


def fallback_line(info: dict[str, Any]) -> str:
    """One warning line when the book runs on pure Python. Empty on the C path."""
    if info.get("path") == "c":
        return ""
    reason = " ".join(str(info.get("reason") or "unknown").split())[:300]
    if reason == "use_pure is set":
        fix = "Fix: unset use_pure in the office config and AGENT_COORD_USE_PURE, then restart the wall."
    else:
        fix = (
            "Fix: pip install --force-reinstall --no-deps --only-binary=:all: "
            "mysql-connector-python, then restart the wall."
        )
    return (
        f"mill: WARNING MySQL driver is pure Python ({reason}); the C extension "
        f"is the default and runs book queries about 2x faster. {fix}"
    )


def warn_once(info: dict[str, Any] | None = None) -> dict[str, Any]:
    """Print the fallback warning to the server log once per process."""
    info = active() if info is None else info
    line = fallback_line(info)
    if line and not _WARNED.is_set():
        _WARNED.set()
        print(line, file=sys.stderr, flush=True)
    return info


def main(argv: list[str] | None = None) -> int:
    """python -m agent_coord.server.records.driver [--require-c]

    Prints the active driver as JSON after the same startup the Wall does.
    --require-c exits 1 on the pure path (CI and host checks).
    """
    import json

    args = list(sys.argv[1:] if argv is None else argv)
    ensure_c_path()
    info = active()
    print(json.dumps(info, sort_keys=True))
    if "--require-c" in args and info.get("path") != "c":
        print(fallback_line(info), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
