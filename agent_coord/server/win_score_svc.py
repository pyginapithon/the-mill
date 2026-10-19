# -*- coding: utf-8 -*-
"""Windows SERVICE: mill-score. Sleep 15m, grep dest logs, mill_score_upsert.

Not mill-wall. Not a 15s HTTP tick. SCM child Popen like mill-wall (nssm-style).
"""
from __future__ import annotations

import argparse
import sys
import threading
from typing import Any

SERVICE_NAME = "mill-score"
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
_stop = threading.Event()
_run_kwargs: dict[str, Any] = {"every": 900, "window": 3600}


def _svc_log(msg: str) -> None:
    import os
    from pathlib import Path

    dest = Path(os.environ.get("AGENT_COORD_MILL_HOME") or (Path.home() / ".mill"))
    try:
        dest.mkdir(parents=True, exist_ok=True)
        with (dest / "mill-score-svc.log").open("a", encoding="utf-8") as f:
            f.write(msg.rstrip() + "\n")
    except Exception:
        print(msg, file=sys.stderr)


def _serve_loop() -> None:
    from agent_coord.server.score_tick import run_loop

    run_loop(every_s=int(_run_kwargs.get("every") or 900), window_s=int(_run_kwargs.get("window") or 3600), stop=_stop)


def run_as_service() -> int:
    if sys.platform != "win32":
        print("win_score_svc is Windows-only", file=sys.stderr)
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
            _set_status(SERVICE_STOP_PENDING, accept=0, wait_hint=5000, checkpoint=1)
            _stop.set()
            return 0
        return 0

    handler = LPHANDLER_FUNCTION_EX(_handler)

    def _service_main(argc: int, argv: Any) -> None:
        global _status_handle
        _status_handle = advapi32.RegisterServiceCtrlHandlerExW(SERVICE_NAME, handler, None)
        if not _status_handle:
            return
        _set_status(SERVICE_RUNNING)
        import os
        import subprocess
        from pathlib import Path

        dest = Path(os.environ.get("AGENT_COORD_MILL_HOME") or (Path.home() / ".mill"))
        dest.mkdir(parents=True, exist_ok=True)
        out = open(dest / "mill-score-svc-out.log", "a", encoding="utf-8")
        env = os.environ.copy()
        env.setdefault("AGENT_COORD_MILL_HOME", str(dest))
        proc = subprocess.Popen(
            [sys.executable] + sys.argv,
            stdout=out,
            stderr=out,
            cwd=str(dest),
            env=env,
        )
        try:
            while not _stop.wait(1.0):
                if proc.poll() is not None:
                    break
        finally:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=8)
                except Exception:
                    proc.kill()
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
        _serve_loop()
        return 0
    print(f"StartServiceCtrlDispatcher failed: {err}", file=sys.stderr)
    return 1


def mill_score_service_binpath(python: str = "") -> str:
    py = str(python or sys.executable).strip() or "python"
    exe = f'"{py}"' if " " in py else py
    return f"{exe} -m agent_coord.server.win_score_svc"


def register_ps1(python: str = "") -> str:
    binpath = mill_score_service_binpath(python=python or sys.executable)
    bin_ps = binpath.replace("'", "''")
    return "\n".join(
        [
            "# mill-score Windows SERVICE (Admin/UAC). Not mill-wall. Not schtasks.",
            '$ErrorActionPreference = "Continue"',
            "$svc = 'mill-score'",
            f"$binPath = '{bin_ps}'",
            "$q = sc.exe query $svc 2>&1",
            "if ($LASTEXITCODE -ne 0) {",
            '  sc.exe create $svc binPath= $binPath start= auto DisplayName= "mill score KPIs" | Out-Null',
            '  sc.exe description $svc "mill-wall.ticks + mill-desk.idle_verbs from dest logs every 15m" | Out-Null',
            "  sc.exe failure $svc reset= 86400 actions= restart/5000/restart/5000/restart/5000 | Out-Null",
            '  Write-Host "sc create mill-score SERVICE"',
            "} else {",
            "  sc.exe config $svc binPath= $binPath start= auto | Out-Null",
            '  Write-Host "sc config mill-score SERVICE"',
            "}",
            "sc.exe start mill-score 2>$null | Out-Null",
            'Write-Host "SCM: mill-score SERVICE"',
            "exit 0",
            "",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="mill-score-svc")
    p.add_argument("--every", type=int, default=900, help="seconds between measures (default 900)")
    p.add_argument("--window", type=int, default=3600, help="lookback seconds (default 3600)")
    args = p.parse_args(argv)
    _run_kwargs["every"] = max(60, int(args.every))
    _run_kwargs["window"] = max(60, int(args.window))
    if sys.platform != "win32":
        _serve_loop()
        return 0
    return run_as_service()


if __name__ == "__main__":
    raise SystemExit(main())
