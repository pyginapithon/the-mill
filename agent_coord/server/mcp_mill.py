# -*- coding: utf-8 -*-
"""Grok Build MCP: mill_wait blocks until mill-wall /ws hint. stdio JSON-RPC."""
from __future__ import annotations

import json
import os
import sys
from typing import Any

PROTOCOL = "2025-03-26"
_FRAME = "lsp"  # lsp Content-Length | ndjson newline


def _dbg(msg: str) -> None:
    try:
        from pathlib import Path

        p = Path.home() / ".mill" / "mcp-mill.debug.log"
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as fh:
            fh.write(msg.rstrip() + "\n")
    except OSError:
        pass
    print(msg, file=sys.stderr, flush=True)


def _mill_has_mcp(mill: str) -> bool:
    import subprocess

    try:
        r = subprocess.run(
            [mill, "mcp-config", "--help"],
            capture_output=True,
            timeout=15,
            text=True,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    blob = (r.stdout or "") + (r.stderr or "")
    return r.returncode == 0 and "mcp-config" in blob


def mill_mcp_argv(owner: str, vendor: str) -> tuple[str, list[str], dict[str, str]]:
    """Command to run mill MCP from any cwd. Prefer mill on PATH (pip install the-mill)."""
    import shutil
    import sys

    who = (owner or "").strip() or "your-desk"
    vend = (vendor or os.environ.get("AGENT_COORD_VENDOR") or "grok-build").strip().lower() or "grok-build"
    env = {"AGENT_COORD_OWNER": who, "AGENT_COORD_VENDOR": vend}
    mill = shutil.which("mill")
    if mill and _mill_has_mcp(mill):
        return mill.replace("\\", "/"), ["mcp"], env
    cmd = sys.executable.replace("\\", "/")
    args = ["-m", "agent_coord.server.mcp_mill"]
    try:
        import agent_coord.server.mcp_mill as _m  # noqa: F401
    except ImportError:
        from pathlib import Path

        here = Path(__file__).resolve()
        env["PYTHONPATH"] = str(here.parents[2] if len(here.parents) >= 2 else here.parent).replace("\\", "/")
    return cmd, args, env


def grok_mcp_toml(owner: str, vendor: str = "grok-build") -> str:
    """Grok ~/.grok/config.toml [mcp_servers.mill]. mill mcp, any folder."""
    cmd, args, env = mill_mcp_argv(owner, vendor)
    args_s = ", ".join(f'"{a}"' for a in args)
    env_s = "\n".join(f'  {k} = "{v}"' for k, v in env.items())
    return (
        f"[mcp_servers.mill]\n"
        f'command = "{cmd}"\n'
        f"args = [{args_s}]\n"
        f"enabled = true\n"
        f"startup_timeout_sec = 8\n"
        f"tool_timeout_sec = 15\n"
        f"tool_timeouts = {{ mill_wait = 8 }}\n"
        f"\n[mcp_servers.mill.env]\n"
        f"{env_s}\n"
    )


def mcp_config_for(owner: str, vendor: str = "") -> str:
    """Snippet for this vendor's MCP file. mill does not auto-detect the AI."""
    v = (vendor or os.environ.get("AGENT_COORD_VENDOR") or "grok-build").strip().lower()
    if v in ("claude", "anthropic", "cursor"):
        cmd, args, env = mill_mcp_argv(owner, v)
        body = {
            "mcpServers": {
                "mill": {
                    "command": cmd,
                    "args": args,
                    "env": env,
                }
            }
        }
        return json.dumps(body, indent=2) + "\n"
    if v in ("antigravity", "gemini", "kimi", "openai", "openai-agents"):
        return (
            f"# mill MCP stdio is the same (`mill mcp`). {v} client file is a volunteer.\n"
            f"# Until then: mill here /ws + connector stub. Grok toml follows:\n"
            + grok_mcp_toml(owner, v)
        )
    return grok_mcp_toml(owner, v or "grok-build")


def wait_for_hint(desk: str, *, timeout_s: float = 8, skip_ping: bool = False) -> dict[str, Any]:
    """One /ws connect. Fail fast if mill-wall is down. Idle is mill connect sit."""
    import asyncio

    from agent_coord.helpers.ident import desk_name
    from agent_coord.client.ws import mill_ws_url

    try:
        import websockets
    except ImportError:
        return {"ok": False, "error": "websockets not installed"}

    from agent_coord.client.tokens import read_session_token

    token = (read_session_token(desk) or "").strip()
    url = mill_ws_url(desk)
    who = desk_name(str(desk or ""))

    async def _go() -> dict[str, Any]:
        kw: dict[str, Any] = {"open_timeout": 2}
        if token:
            kw["additional_headers"] = {"Authorization": "Bearer " + token}
        try:
            conn = websockets.connect(url, **kw)
        except TypeError:
            kw.pop("additional_headers", None)
            if token:
                kw["extra_headers"] = {"Authorization": "Bearer " + token}
            conn = websockets.connect(url, **kw)
        try:
            async with conn as ws:
                deadline = asyncio.get_event_loop().time() + max(1.0, min(float(timeout_s), 8.0))
                while True:
                    left = deadline - asyncio.get_event_loop().time()
                    if left <= 0:
                        return {"ok": False, "error": "timeout", "url": url, "desk": who}
                    raw = await asyncio.wait_for(ws.recv(), timeout=left)
                    try:
                        msg = json.loads(raw)
                    except json.JSONDecodeError:
                        msg = {"raw": raw}
                    if skip_ping and str(msg.get("hint") or "") == "PING":
                        continue
                    return {"ok": True, "hint": msg, "desk": who, "url": url.split("?")[0]}
        except Exception as e:
            return {"ok": False, "error": f"mill-wall down: {type(e).__name__}", "desk": who}

    return asyncio.run(_go())


def _tools() -> list[dict[str, Any]]:
    return [
        {
            "name": "mill_wait",
            "description": (
                "Block until mill-wall backchannel sends a hint for this desk "
                "({type,id,hint} MAIL/TODO/PING). Then mill inbox or mill todo. "
                "Then mill inbox or mill todo. Idle is mill connect sit, not leftover."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "timeout_s": {"type": "number", "default": 60},
                    "skip_ping": {
                        "type": "boolean",
                        "default": False,
                        "description": "Ignore heartbeat PING; wait for MAIL/TODO.",
                    },
                    "owner": {
                        "type": "string",
                        "description": "Desk name; default AGENT_COORD_OWNER",
                    },
                },
            },
        },
    ]


def _call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if name == "mill_wait":
        owner = str(arguments.get("owner") or os.environ.get("AGENT_COORD_OWNER") or "").strip()
        if not owner:
            return {"ok": False, "error": "owner or AGENT_COORD_OWNER required"}
        timeout_s = min(float(arguments.get("timeout_s") or 8), 8)
        skip_ping = bool(arguments.get("skip_ping"))
        return wait_for_hint(owner, timeout_s=timeout_s, skip_ping=skip_ping)
    return {"ok": False, "error": f"unknown tool {name}"}


def _read_stdio() -> dict[str, Any] | None:
    global _FRAME
    line = sys.stdin.buffer.readline()
    if not line:
        return None
    if line.lower().startswith(b"content-length:"):
        _FRAME = "lsp"
        n = int(line.split(b":", 1)[1].strip())
        while True:
            hdr = sys.stdin.buffer.readline()
            if hdr in (b"\r\n", b"\n", b""):
                break
        raw = sys.stdin.buffer.read(n)
        return json.loads(raw.decode("utf-8"))
    _FRAME = "ndjson"
    return json.loads(line.decode("utf-8"))


def _write_stdio(msg: dict[str, Any]) -> None:
    blob = json.dumps(msg, default=str).encode("utf-8")
    if _FRAME == "ndjson":
        sys.stdout.buffer.write(blob + b"\n")
    else:
        sys.stdout.buffer.write(f"Content-Length: {len(blob)}\r\n\r\n".encode("ascii"))
        sys.stdout.buffer.write(blob)
    sys.stdout.buffer.flush()


def handle(msg: dict[str, Any]) -> dict[str, Any] | None:
    mid = msg.get("id")
    method = str(msg.get("method") or "")
    params = msg.get("params") or {}
    if method == "initialize":
        ver = str(params.get("protocolVersion") or PROTOCOL)
        return {
            "jsonrpc": "2.0",
            "id": mid,
            "result": {
                "protocolVersion": ver,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "mill", "version": "0.4.0"},
            },
        }
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": mid, "result": {"tools": _tools()}}
    if method == "tools/call":
        name = str(params.get("name") or "")
        args = params.get("arguments") or {}
        out = _call_tool(name, args if isinstance(args, dict) else {})
        text = json.dumps(out, default=str)
        return {
            "jsonrpc": "2.0",
            "id": mid,
            "result": {"content": [{"type": "text", "text": text}], "isError": not out.get("ok", True)},
        }
    if method == "ping":
        return {"jsonrpc": "2.0", "id": mid, "result": {}}
    return {
        "jsonrpc": "2.0",
        "id": mid,
        "error": {"code": -32601, "message": f"method not found: {method}"},
    }


def main() -> int:
    _dbg("mill mcp start")
    while True:
        try:
            msg = _read_stdio()
        except Exception as e:
            _dbg(f"read fail: {e}")
            return 1
        if msg is None:
            _dbg("stdin eof")
            return 0
        _dbg(f"in {msg.get('method')} id={msg.get('id')} frame={_FRAME}")
        try:
            resp = handle(msg)
        except Exception as e:
            _dbg(f"handle fail: {e}")
            resp = {
                "jsonrpc": "2.0",
                "id": msg.get("id"),
                "error": {"code": -32000, "message": str(e)[:400]},
            }
        if resp is not None:
            _write_stdio(resp)
            _dbg(f"out {resp.get('result') and 'ok' or resp.get('error')}")


if __name__ == "__main__":
    raise SystemExit(main())
