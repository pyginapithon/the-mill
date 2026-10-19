# -*- coding: utf-8 -*-
"""Local mill route chain: this desk's programs, in add order (not mill-wall).

Durable: ~/.mill/session/<desk>.route  (key = value lines, file order).
Re-read on every HINT. PING never enters. * sits where it was added.
Empty value suppresses and stops. The hub does not walk this list.
"""
from __future__ import annotations

import contextvars
import json
import os
import shlex
import subprocess
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Iterator, Literal

from agent_coord.helpers.ident import desk as slug_desk

Decision = Literal["handled", "next", "suppress"]
Mark = Literal["handled", "next", "fail"]
_EXIT_SINK: contextvars.ContextVar[Callable[[dict[str, Any]], None] | None] = contextvars.ContextVar(
    "mill_route_exit_sink", default=None
)
MARK_NEXT = "not-mine"


def route_path(desk: str) -> Path:
    from agent_coord.client.offices import desk_local_file
    from agent_coord.config import mill_home

    hosted = desk_local_file(desk, "route")
    if hosted is not None:
        return hosted
    who = slug_desk(desk)
    dest = mill_home() / "session"
    dest.mkdir(parents=True, exist_ok=True)
    return dest / f"{who}.route"


def route_key(msg: dict[str, Any]) -> str:
    """type:hint, or mail:MAIL for a letter {kind: mail}."""
    got = str(msg.get("route") or "").strip()
    if got:
        return got
    kind = str(msg.get("kind") or "").strip().lower()
    if kind == "mail":
        return "mail:MAIL"
    typ = str(msg.get("type") or "").strip()
    hint = str(msg.get("hint") or "").strip()
    if typ and hint:
        return f"{typ}:{hint}"
    return hint or typ or ""


def _pairs(routes: Any) -> list[tuple[str, str]]:
    if isinstance(routes, dict):
        seq: Iterator[tuple[Any, Any]] = iter(routes.items())
    else:
        seq = iter(routes or [])
    out: list[tuple[str, str]] = []
    index: dict[str, int] = {}
    for item in seq:
        key, raw = item
        name = str(key or "").strip()
        if not name:
            continue
        val = "" if raw is None else str(raw)
        if name in index:
            out[index[name]] = (name, val)
            continue
        index[name] = len(out)
        out.append((name, val))
    return out


def load_routes(desk: str) -> list[tuple[str, str]]:
    """This desk's chain in file order. A repeated key keeps its place."""
    p = route_path(desk)
    if not p.is_file():
        return []
    rows: list[tuple[str, str]] = []
    index: dict[str, int] = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        key, raw = s.split("=", 1)
        key = key.strip()
        if not key:
            continue
        val = raw.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1].replace('\\"', '"').replace("\\\\", "\\")
        if key in index:
            rows[index[key]] = (key, val)
            continue
        index[key] = len(rows)
        rows.append((key, val))
    return rows


def save_routes(desk: str, routes: Any) -> Path:
    """Write the chain in the order given. Do not sort * to the end."""
    p = route_path(desk)
    lines = ["# mill route - chain order, key = argv (empty value = suppress)", ""]
    for key, val in _pairs(routes):
        lines.append(f"{key} = {val}")
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


def add_route(desk: str, key: str, argv: str) -> Path:
    """Append KEY. A key already in the list is replaced and keeps its place."""
    name = str(key or "").strip()
    if not name:
        raise ValueError("key required")
    routes = load_routes(desk)
    val = "" if argv is None else str(argv)
    for i, (got, _) in enumerate(routes):
        if got == name:
            routes[i] = (name, val)
            return save_routes(desk, routes)
    routes.append((name, val))
    return save_routes(desk, routes)


def rm_route(desk: str, key: str) -> Path:
    """Remove one key. A missing key raises KeyError and does not clear the list."""
    name = str(key or "").strip()
    routes = load_routes(desk)
    kept = [(k, v) for k, v in routes if k != name]
    if len(kept) == len(routes):
        raise KeyError(name)
    return save_routes(desk, kept)


def list_lines(desk: str) -> list[str]:
    """One line per entry: key, then the program, or suppress."""
    lines: list[str] = []
    for key, val in load_routes(desk):
        shown = val if str(val).strip() else "suppress"
        lines.append(f"{key} {shown}")
    return lines


def _matching(desk: str, msg: dict[str, Any]) -> list[tuple[str, str]]:
    want = route_key(msg)
    out: list[tuple[str, str]] = []
    for key, raw in load_routes(desk):
        if key == "*" or (want and key == want):
            out.append((key, raw))
    return out


# Hub frame on stdin stays small. A route cmd is local argv, never a shell line.
FRAME_MAX = 8192


def split_cmd(cmd: str) -> list[str]:
    """Argv for a route or spawn command.

    Windows stores `mill route` with list2cmdline. CommandLineToArgvW is the
    matching split. shlex posix=False keeps quotes; posix=True eats backslashes.
    """
    text = (cmd or "").strip()
    if not text:
        return []
    if os.name != "nt":
        return shlex.split(text, posix=True)
    import ctypes
    from ctypes import wintypes

    argc = ctypes.c_int(0)
    shell32 = ctypes.WinDLL("shell32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    shell32.CommandLineToArgvW.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_int)]
    shell32.CommandLineToArgvW.restype = ctypes.POINTER(wintypes.LPWSTR)
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    kernel32.LocalFree.restype = ctypes.c_void_p
    buf = shell32.CommandLineToArgvW(text, ctypes.byref(argc))
    if not buf:
        raise ValueError("cmd did not split")
    try:
        return [buf[i] for i in range(int(argc.value))]
    finally:
        kernel32.LocalFree(ctypes.cast(buf, ctypes.c_void_p))


def _spawn_kwargs() -> dict[str, Any]:
    kw: dict[str, Any] = {}
    if os.name == "nt":
        flags = 0
        flags |= getattr(subprocess, "CREATE_NO_WINDOW", 0)
        flags |= getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        if flags:
            kw["creationflags"] = flags
    else:
        kw["start_new_session"] = True
    return kw


def popen_hint(cmd: str, raw: bytes) -> None:
    """Start cmd with the HINT frame on stdin. Do not wait. No shell."""
    if len(raw) > FRAME_MAX:
        raise ValueError(f"HINT frame {len(raw)} bytes exceeds {FRAME_MAX}")
    argv = split_cmd(cmd)
    if not argv:
        raise ValueError("empty cmd")
    kw = _spawn_kwargs()
    kw["stdin"] = subprocess.PIPE
    kw["stdout"] = subprocess.DEVNULL
    kw["stderr"] = subprocess.DEVNULL
    proc = subprocess.Popen(argv, **kw)
    try:
        if proc.stdin is None:
            raise RuntimeError("redirector stdin was not piped")
        proc.stdin.write(raw)
        proc.stdin.close()
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass
        raise


def spawn_route(cmd: str, msg: dict[str, Any]) -> None:
    """Fire-and-forget. HINT JSON on stdin. Do not wait."""
    c = (cmd or "").strip()
    if not c:
        raise ValueError("empty route cmd")
    raw = json.dumps(msg, default=str, separators=(",", ":")).encode("utf-8")
    popen_hint(c, raw)


def _last_line(out: bytes | str | None) -> str:
    text = out.decode("utf-8", "replace") if isinstance(out, (bytes, bytearray)) else str(out or "")
    last = ""
    for line in text.splitlines():
        s = line.strip()
        if s:
            last = s
    return last


def run_program(cmd: str, msg: dict[str, Any]) -> tuple[Mark, int]:
    """Run one redirector and wait for its exit. Do not spawn the vendor.

    Exit 0 and a last stdout line of not-mine: next.
    Exit 0 otherwise: handled. An existing program that exits 0 stops the chain.
    Non-zero: fail. The caller writes the exit line and tries the next redirector.
    """
    c = (cmd or "").strip()
    if not c:
        raise ValueError("empty route cmd")
    raw = json.dumps(msg, default=str, separators=(",", ":")).encode("utf-8")
    if len(raw) > FRAME_MAX:
        raise ValueError(f"HINT frame {len(raw)} bytes exceeds {FRAME_MAX}")
    argv = split_cmd(c)
    if not argv:
        raise ValueError("empty cmd")
    kw = _spawn_kwargs()
    kw["stdin"] = subprocess.PIPE
    kw["stdout"] = subprocess.PIPE
    kw["stderr"] = subprocess.DEVNULL
    proc = subprocess.Popen(argv, **kw)
    try:
        out, _err = proc.communicate(raw)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass
        raise
    code = int(proc.returncode if proc.returncode is not None else 1)
    if code != 0:
        return "fail", code
    if _last_line(out) == MARK_NEXT:
        return "next", 0
    return "handled", 0


@contextmanager
def bind_exit(sink: Callable[[dict[str, Any]], None] | None):
    """Where a non-zero exit notice goes. The hub is not this sink."""
    token = _EXIT_SINK.set(sink)
    try:
        yield
    finally:
        _EXIT_SINK.reset(token)


def _emit_exit(key: str, hint_id: Any, code: int) -> None:
    try:
        hid = int(hint_id or 0)
    except (TypeError, ValueError):
        hid = 0
    notice = {"exit": 1, "frame": {"route": str(key), "id": hid, "exit": int(code)}}
    sink = _EXIT_SINK.get()
    if sink is None:
        return
    try:
        sink(notice)
    except Exception:
        return


def try_route(desk: str, msg: dict[str, Any]) -> Decision:
    """Walk this desk's chain. Return handled, next, or suppress.

    Does not spawn the vendor. PING does not enter.
    Empty value stops the chain. The first handled program stops it.
    not-mine and a non-zero exit try the next redirector.
    """
    if str((msg or {}).get("hint") or "") == "PING":
        return "suppress"
    entries = _matching(desk, msg or {})
    if not entries:
        return "next"
    all_next = True
    for key, raw in entries:
        if not str(raw or "").strip():
            return "suppress"
        mark, code = run_program(raw, msg)
        if mark == "handled":
            return "handled"
        if mark == "fail":
            all_next = False
            _emit_exit(key, (msg or {}).get("id"), code)
    # Vendor runs only when every redirector returned not-mine.
    return "next" if all_next else "handled"
