# -*- coding: utf-8 -*-
"""Windows SERVICE host for mill wall API (nssm-free, no leftover console).

SCM starts: python -m agent_coord.server.win_wall_svc [--bind ...] [--port ...] [--api-only]
Closing a window must not kill the API (that was the schtasks 0xC000013A failure mode).
"""
from __future__ import annotations

import argparse
import sys
import threading
from typing import Any

SERVICE_NAME = "mill-wall"
SERVICE_WIN32_OWN_PROCESS = 0x00000010
SERVICE_ACCEPT_STOP = 0x00000001
SERVICE_ACCEPT_SHUTDOWN = 0x00000004
SERVICE_RUNNING = 0x00000004
SERVICE_STOP_PENDING = 0x00000003
SERVICE_STOPPED = 0x00000001
SERVICE_CONTROL_STOP = 0x00000001
SERVICE_CONTROL_SHUTDOWN = 0x00000005
ERROR_FAILED_SERVICE_CONTROLLER_CONNECT = 1063

_status_handle: Any = None
_httpd: Any = None
_stop = threading.Event()
_run_kwargs: dict[str, Any] = {
    "bind": "127.0.0.1",
    "port": 8765,
    "api_only": False,
}


def _svc_log(msg: str) -> None:
    import os
    from datetime import datetime, timezone
    from pathlib import Path

    dest = Path(os.environ.get("AGENT_COORD_MILL_HOME") or (Path.home() / ".mill"))
    line = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ ") + msg.rstrip()
    try:
        dest.mkdir(parents=True, exist_ok=True)
        with (dest / "mill-wall-svc.log").open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        try:
            print(line, file=sys.stderr)
        except Exception:
            pass


class _TeeIO:
    """No TTY. Every write flushed to mill-wall-svc-out.log (and errors to mill-wall-svc.log)."""

    encoding = "utf-8"

    def __init__(self, path, *, error: bool = False) -> None:
        self._path = path
        self._error = error

    def isatty(self) -> bool:
        return False

    def write(self, s: str) -> int:
        if not s:
            return 0
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with self._path.open("a", encoding="utf-8") as f:
                f.write(s)
                f.flush()
        except Exception:
            pass
        if self._error:
            try:
                _svc_log(s if s.endswith("\n") else s)
            except Exception:
                pass
        return len(s)

    def flush(self) -> None:
        return None

    def fileno(self) -> int:
        raise OSError("no console")

    def readable(self) -> bool:
        return False

    def writable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return False


def _no_console_stdio() -> None:
    """Windows SERVICE / no-console: uvicorn must not probe a TTY. Highest precedence."""
    import os
    from pathlib import Path

    dest = Path(os.environ.get("AGENT_COORD_MILL_HOME") or (Path.home() / ".mill"))
    out_path = dest / "mill-wall-svc-out.log"
    sys.stdout = _TeeIO(out_path, error=False)
    sys.stderr = _TeeIO(out_path, error=True)
    sys.__stdout__ = sys.stdout
    sys.__stderr__ = sys.stderr


def _serve_wall() -> None:
    global _httpd
    import os

    _no_console_stdio()
    from agent_coord.config import settings
    from .asgi import run_uvicorn, shutdown_uvicorn
    from agent_coord.lib.observe import parse_roots

    s = settings()
    host = str(_run_kwargs.get("bind") or s["dashboard_bind"] or "127.0.0.1")
    port = int(_run_kwargs.get("port") if _run_kwargs.get("port") is not None else s["dashboard_port"])
    api_only = bool(_run_kwargs.get("api_only", True))
    _svc_log(f"serve start host={host} port={port} api_only={api_only} pid={os.getpid()}")
    _httpd = shutdown_uvicorn
    try:
        run_uvicorn(host, port, parse_roots(), api_only=api_only)
        _svc_log("serve stop clean")
    except Exception:
        import traceback

        _svc_log("serve crash\n" + traceback.format_exc())
        raise
    finally:
        _httpd = None


def run_as_service() -> int:
    """Register with SCM and host the wall. Console fallback when not started by SCM."""
    if sys.platform != "win32":
        print("win_wall_svc is Windows-only", file=sys.stderr)
        return 2
    import ctypes
    from ctypes import wintypes

    LPSERVICE_MAIN_FUNCTION = ctypes.WINFUNCTYPE(None, wintypes.DWORD, ctypes.POINTER(wintypes.LPWSTR))
    LPHANDLER_FUNCTION_EX = ctypes.WINFUNCTYPE(
        wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID, wintypes.LPVOID
    )

    class SERVICE_STATUS(ctypes.Structure):
        _fields_ = [
            ("dwServiceType", wintypes.DWORD),
            ("dwCurrentState", wintypes.DWORD),
            ("dwControlsAccepted", wintypes.DWORD),
            ("dwWin32ExitCode", wintypes.DWORD),
            ("dwServiceSpecificExitCode", wintypes.DWORD),
            ("dwCheckPoint", wintypes.DWORD),
            ("dwWaitHint", wintypes.DWORD),
        ]

    class SERVICE_TABLE_ENTRY(ctypes.Structure):
        _fields_ = [
            ("lpServiceName", wintypes.LPWSTR),
            ("lpServiceProc", LPSERVICE_MAIN_FUNCTION),
        ]

    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    advapi32.StartServiceCtrlDispatcherW.argtypes = [ctypes.POINTER(SERVICE_TABLE_ENTRY)]
    advapi32.StartServiceCtrlDispatcherW.restype = wintypes.BOOL
    advapi32.RegisterServiceCtrlHandlerExW.argtypes = [
        wintypes.LPCWSTR,
        LPHANDLER_FUNCTION_EX,
        wintypes.LPVOID,
    ]
    advapi32.RegisterServiceCtrlHandlerExW.restype = wintypes.HANDLE
    advapi32.SetServiceStatus.argtypes = [wintypes.HANDLE, ctypes.POINTER(SERVICE_STATUS)]
    advapi32.SetServiceStatus.restype = wintypes.BOOL

    def _set_status(
        state: int,
        *,
        accept: int = SERVICE_ACCEPT_STOP | SERVICE_ACCEPT_SHUTDOWN,
        wait_hint: int = 0,
        checkpoint: int = 0,
    ) -> None:
        if not _status_handle:
            return
        st = SERVICE_STATUS()
        st.dwServiceType = SERVICE_WIN32_OWN_PROCESS
        st.dwCurrentState = state
        st.dwControlsAccepted = accept if state == SERVICE_RUNNING else 0
        st.dwWin32ExitCode = 0
        st.dwServiceSpecificExitCode = 0
        st.dwCheckPoint = checkpoint
        st.dwWaitHint = wait_hint
        advapi32.SetServiceStatus(_status_handle, ctypes.byref(st))

    def _handler(control: int, event_type: int, event_data: Any, context: Any) -> int:
        if control in (SERVICE_CONTROL_STOP, SERVICE_CONTROL_SHUTDOWN):
            _svc_log(f"scm stop control={control}")
            _set_status(SERVICE_STOP_PENDING, accept=0, wait_hint=5000, checkpoint=1)
            _stop.set()
            stopper = _httpd
            if stopper is not None:
                try:
                    stopper()
                except Exception:
                    pass
            return 0
        return 0

    handler = LPHANDLER_FUNCTION_EX(_handler)

    def _service_main(argc: int, argv: Any) -> None:
        global _status_handle
        try:
            _status_handle = advapi32.RegisterServiceCtrlHandlerExW(SERVICE_NAME, handler, None)
            if not _status_handle:
                _svc_log("scm RegisterServiceCtrlHandlerEx failed")
                return
            _set_status(SERVICE_RUNNING)
            _scm_child()
        except Exception:
            import traceback

            _svc_log("scm main crash\n" + traceback.format_exc())
            try:
                _set_status(SERVICE_STOPPED)
            except Exception:
                pass

    def _scm_child() -> None:
        # uvicorn inside the SCM process hangs TLS on Windows (Proactor/no console).
        # Spawn a normal python child - same trick as nssm / SO 56825574.
        import os
        import subprocess
        from pathlib import Path

        dest = Path(os.environ.get("AGENT_COORD_MILL_HOME") or (Path.home() / ".mill"))
        dest.mkdir(parents=True, exist_ok=True)
        out = open(dest / "mill-wall-svc-out.log", "a", encoding="utf-8")
        child_argv = [sys.executable] + sys.argv
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        _svc_log(f"scm parent pid={os.getpid()} spawn child argv={child_argv!r}")
        proc = subprocess.Popen(
            child_argv,
            stdout=out,
            stderr=out,
            stdin=subprocess.DEVNULL,
            cwd=str(dest),
            env=env,
        )
        _svc_log(f"scm child pid={proc.pid}")
        try:
            while not _stop.wait(1.0):
                if proc.poll() is not None:
                    _svc_log(f"scm child exit code={proc.returncode}")
                    break
        finally:
            if proc.poll() is None:
                _svc_log("scm terminate child")
                proc.terminate()
                try:
                    proc.wait(timeout=8)
                except Exception:
                    proc.kill()
                    _svc_log("scm kill child")
            try:
                out.close()
            except Exception:
                pass
            _set_status(SERVICE_STOP_PENDING, accept=0, wait_hint=3000, checkpoint=2)
            _set_status(SERVICE_STOPPED)

    service_main = LPSERVICE_MAIN_FUNCTION(_service_main)
    table = (SERVICE_TABLE_ENTRY * 2)()
    table[0].lpServiceName = SERVICE_NAME
    table[0].lpServiceProc = service_main
    table[1].lpServiceName = None
    table[1].lpServiceProc = LPSERVICE_MAIN_FUNCTION()
    ok = advapi32.StartServiceCtrlDispatcherW(ctypes.cast(table, ctypes.POINTER(SERVICE_TABLE_ENTRY)))
    if ok:
        return 0
    err = ctypes.get_last_error()
    if err == ERROR_FAILED_SERVICE_CONTROLLER_CONNECT:
        _svc_log("not scm; console/child fallback _serve_wall")
        try:
            _serve_wall()
            return 0
        except Exception:
            import traceback

            _svc_log("fallback crash\n" + traceback.format_exc())
            return 1
    print(f"StartServiceCtrlDispatcher failed: {err}", file=sys.stderr)
    return 1


def main(argv: list[str] | None = None) -> int:
    if sys.platform != "win32":
        print("win_wall_svc is Windows-only", file=sys.stderr)
        return 2
    p = argparse.ArgumentParser(prog="mill-wall-svc")
    p.add_argument("--bind", default=None)
    p.add_argument("--port", type=int, default=None)
    p.add_argument("--api-only", action="store_true", default=False)
    p.add_argument("--no-api-only", action="store_true")
    args = p.parse_args(argv)
    from agent_coord.config import settings

    s = settings()
    _run_kwargs["bind"] = args.bind or s["dashboard_bind"]
    _run_kwargs["port"] = int(s["dashboard_port"] if args.port is None else args.port)
    _run_kwargs["api_only"] = False if args.no_api_only else bool(args.api_only)
    return run_as_service()


if __name__ == "__main__":
    raise SystemExit(main())
