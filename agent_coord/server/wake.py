"""Optional mill wake-hook URL + fire-and-forget POST."""
from __future__ import annotations

import json
import os
from typing import Any


def wake_url() -> str:
    """Optional mill wake hook URL. Empty = no POST (fail soft)."""
    try:
        from agent_coord.config import settings

        return str(settings().get("wake_url") or "").strip()
    except Exception:
        return (os.environ.get("AGENT_COORD_WAKE_URL") or "").strip()


def webhook_key() -> str:
    """Key for a host webhook POST. Empty means send no auth headers.

    The join row has endpoint_url and no key column. Read at POST time.
    Not the wake URL.
    """
    try:
        from agent_coord.config import settings

        return str(settings().get("webhook_key") or "").strip()
    except Exception:
        return (os.environ.get("AGENT_COORD_WEBHOOK_KEY") or "").strip()


def _log_hook_fail(desk: str, hint_id: int | None, *, status: int | None = None, exc_type: str = "") -> None:
    """One failure line. Desk and hint id when the caller has them. Never the endpoint URL."""
    parts = ["webhook fail"]
    if desk:
        parts.append(f"desk={desk}")
    if hint_id is not None:
        parts.append(f"id={hint_id}")
    if status is not None:
        parts.append(f"status={int(status)}")
    else:
        parts.append(f"err={exc_type or 'Exception'}")
    line = " ".join(parts)
    try:
        from agent_coord.server.push import _bc_log

        _bc_log(line)
    except Exception:
        return


def _post_once(
    url: str,
    payload: dict[str, Any],
    *,
    timeout: float,
    key: str | None,
    desk: str,
    hint_id: int | None,
) -> bool:
    """One HTTP POST. Never raises. True only when the response is 2xx."""
    u = (url or "").strip()
    if not u:
        return False
    try:
        import urllib.error
        import urllib.request

        raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        secret = (key or "").strip()
        if secret:
            headers["Authorization"] = "Bearer " + secret
            headers["X-Automation-Key"] = secret
        req = urllib.request.Request(
            u,
            data=raw,
            headers=headers,
            method="POST",
        )
        # urllib capitalizes custom header names. Keep the contract spelling.
        mangled = "X-automation-key"
        if secret and mangled in req.headers:
            req.headers["X-Automation-Key"] = req.headers.pop(mangled)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            resp.read(256)
            status = getattr(resp, "status", None)
            if status is None:
                status = getattr(resp, "code", None)
            if status is not None and not 200 <= int(status) <= 299:
                _log_hook_fail(desk, hint_id, status=int(status))
                return False
        return True
    except urllib.error.HTTPError as e:
        _log_hook_fail(desk, hint_id, status=int(e.code))
        return False
    except Exception as e:
        _log_hook_fail(desk, hint_id, exc_type=type(e).__name__)
        return False


def fire_wake_hook(
    url: str,
    payload: dict[str, Any],
    *,
    timeout: float = 2.0,
    key: str | None = None,
    desk: str = "",
    hint_id: int | None = None,
) -> bool:
    """HTTP POST JSON. Never raises. True only when the response is 2xx.

    A key adds Authorization Bearer and X-Automation-Key. An empty key adds neither.
    Timeout, connection error, or non-2xx returns False and logs status or error type.
    A body that already carries idem retries that failure once. A body without it
    does not retry.
    """
    from agent_coord.server.poke_key import FIELD

    ok = _post_once(
        url,
        payload,
        timeout=timeout,
        key=key,
        desk=desk,
        hint_id=hint_id,
    )
    if ok:
        return True
    if not str((payload or {}).get(FIELD) or "").strip():
        return False
    if not (url or "").strip():
        return False
    return _post_once(
        url,
        payload,
        timeout=timeout,
        key=key,
        desk=desk,
        hint_id=hint_id,
    )
