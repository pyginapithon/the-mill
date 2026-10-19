# -*- coding: utf-8 -*-
"""mill wall-check: Wall HTML + Office agents vs a stale ?projects= filter. Cheap JSON, no dump."""
from __future__ import annotations

import json
import ssl
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

from agent_coord.install.packver import package_version


def _ssl_ctx(ca: Path | None = None) -> ssl.SSLContext:
    from agent_coord.install import mill_ca_crt

    path = Path(ca) if ca is not None else mill_ca_crt()
    if path.name.lower() == "wall.crt":
        raise ValueError("never import wall.crt; use mill ca.crt")
    if path.is_file():
        return ssl.create_default_context(cafile=str(path))
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _get(url: str, accept: str, ctx: ssl.SSLContext, urlopen: Any = None) -> tuple[int, str, bytes]:
    opener = urlopen or urllib.request.urlopen
    req = urllib.request.Request(url, headers={"Accept": accept, "User-Agent": "mill-wall-check"})
    with opener(req, context=ctx, timeout=20) as r:
        ct = (r.headers.get("content-type") or "").split(";")[0]
        return int(r.status), ct, r.read()


def _keep(rows: list, project: str) -> list:
    return [r for r in (rows or []) if str(r.get("project_id") or "") == project]


def filter_hides_live(*, live_agents: int, filtered_agents: int) -> bool:
    return int(filtered_agents) == 0 and int(live_agents) > 0


def wall_check(
    *,
    base: str = "",
    project_filter: str = "the-mill",
    expect_empty: bool = False,
    urlopen: Any = None,
    ssl_context: Any = None,
    ca: Path | None = None,
) -> tuple[dict[str, Any], int]:
    """Compare Wall HTML + GET /api/v1/agents?project=Office. Exit 2 if --expect-empty and the filter zeros a live office."""
    from agent_coord.install import share_wall_urls

    root = (base or "").rstrip("/")
    if not root:
        urls = [u for u in share_wall_urls() if str(u).startswith("https://")]
        root = (urls[0] if urls else "https://127.0.0.1/").rstrip("/")
    ctx = ssl_context if ssl_context is not None else _ssl_ctx(ca)
    mill_ver = package_version()
    out: dict[str, Any] = {
        "base": root,
        "ok": False,
        "bug": None,
        "mill_version": mill_ver,
        "correct_url": f"{root}/#session",
    }
    try:
        st, ct, body = _get(root + "/", "text/html", ctx, urlopen=urlopen)
        html = body.decode("utf-8", "replace")
        out["html"] = {
            "status": st,
            "bytes": len(body),
            "content_type": ct,
            "pane_session": 'id="pane-session"' in html,
            "here": 'id="here"' in html,
            "pane_mail": 'id="pane-mail"' in html,
        }
    except Exception as e:
        out["html_error"] = f"{type(e).__name__}: {e}"[:200]
        return out, 1

    try:
        st, ct, body = _get(
            root + "/api/v1/agents?project=Office",
            "application/json",
            ctx,
            urlopen=urlopen,
        )
        floor = json.loads(body.decode())
        agents = floor.get("agents") or []
        mailbox = floor.get("mailbox") or []
        live = [a for a in agents if a.get("alive")]
        floor_ver = str(floor.get("version") or "")
        out["api"] = {
            "status": st,
            "bytes": len(body),
            "content_type": ct,
            "live_agents": int(floor.get("live_agents") or len(live)),
            "agents": len(agents),
            "mailbox": len(mailbox),
            "version": floor_ver,
            "agent_projects": dict(Counter(a.get("project_id") for a in agents)),
            "mail_projects": dict(Counter(m.get("project_id") for m in mailbox)),
        }
        stale = project_filter
        out["filter"] = {
            "projects": stale,
            "agents": len(_keep(agents, stale)),
            "mailbox": len(_keep(mailbox, stale)),
            "url": f"{root}/?projects={stale}#session",
        }
        out["version_match"] = bool(floor_ver) and floor_ver == mill_ver
    except Exception as e:
        out["api_error"] = f"{type(e).__name__}: {e}"[:200]
        return out, 1

    html_ok = out["html"]["status"] == 200 and out["html"]["pane_session"]
    api_ok = out["api"]["status"] == 200 and out["api"]["live_agents"] > 0
    hides = filter_hides_live(
        live_agents=out["api"]["live_agents"],
        filtered_agents=out["filter"]["agents"],
    )
    out["ok"] = bool(html_ok and api_ok)
    bugs: list[str] = []
    if not floor_ver:
        bugs.append("floor.version missing")
        out["ok"] = False
    elif not out["version_match"]:
        bugs.append(f"floor.version={floor_ver!r} != mill {mill_ver}")
    if hides:
        bugs.append(
            f"?projects={project_filter} hides live {out['api']['agent_projects']} "
            "desks/mail while Office agents are healthy"
        )
    out["bug"] = "; ".join(bugs) if bugs else None
    if not out["ok"]:
        return out, 1
    if expect_empty and hides:
        return out, 2
    return out, 0
