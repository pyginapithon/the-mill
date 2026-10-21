"""Optional mill wake-hook URL + fire-and-forget POST, and desk webhook wake (#618).

A desk picks webhook delivery at mill join: the URL and the desk's own key live
on its join row. The key is read only at POST time (mill_join_wake_target) and is
never returned by a read, a log line or an error. The URL is https only, on a
host in this wall's wake_hosts allowlist, never an IP literal, and every address
it resolves to must be public. Redirects are never followed.

A POST is a doorbell: one per desk until that desk connects or WAKE_WINDOW_S
passes. Every hint and letter stays in the desk's push queue as missed either
way, so the woken desk's mill connect sync hands over all of them and its
redirector chain walks each one there (the same walk as a /ws hint).
"""
from __future__ import annotations

import json
import os
import threading
import urllib.request
from typing import Any


def wake_url() -> str:
    """Optional mill wake hook URL. Empty = no POST (fail soft)."""
    try:
        from agent_coord.config import settings

        return str(settings().get("wake_url") or "").strip()
    except Exception:
        return (os.environ.get("AGENT_COORD_WAKE_URL") or "").strip()


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


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """A wake POST never follows a redirect: the allowlist checked the first URL only."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D401
        return None


def _open(req, timeout: float):
    """One request through an opener that refuses redirects (a 3xx is a failure)."""
    import urllib.request

    return urllib.request.build_opener(_NoRedirect).open(req, timeout=timeout)


def _post_status(
    url: str,
    payload: dict[str, Any],
    *,
    timeout: float,
    key: str | None,
    desk: str,
    hint_id: int | None,
    quiet: bool = False,
) -> tuple[int | None, str]:
    """One HTTP POST. Never raises. (status, "") or (None, error type).
    quiet: the caller logs the outcome itself (a desk wake logs one line, #625)."""
    u = (url or "").strip()
    if not u:
        return None, "NoURL"
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
        with _open(req, timeout) as resp:
            resp.read(256)
            status = getattr(resp, "status", None)
            if status is None:
                status = getattr(resp, "code", None)
            status = 200 if status is None else int(status)
            if not 200 <= status <= 299 and not quiet:
                _log_hook_fail(desk, hint_id, status=status)
            return status, ""
    except urllib.error.HTTPError as e:
        if not quiet:
            _log_hook_fail(desk, hint_id, status=int(e.code))
        return int(e.code), ""
    except Exception as e:
        if not quiet:
            _log_hook_fail(desk, hint_id, exc_type=type(e).__name__)
        return None, type(e).__name__


def _fire(
    url: str,
    payload: dict[str, Any],
    *,
    timeout: float,
    key: str | None,
    desk: str,
    hint_id: int | None,
    quiet: bool = False,
) -> tuple[int | None, str]:
    """POST once; a body that carries idem retries a failure once. The last (status, error)."""
    from agent_coord.server.poke_key import FIELD

    status, err = _post_status(url, payload, timeout=timeout, key=key, desk=desk, hint_id=hint_id, quiet=quiet)
    if status is not None and 200 <= status <= 299:
        return status, err
    if not str((payload or {}).get(FIELD) or "").strip() or not (url or "").strip():
        return status, err
    return _post_status(url, payload, timeout=timeout, key=key, desk=desk, hint_id=hint_id, quiet=quiet)


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
    status, _err = _fire(url, payload, timeout=timeout, key=key, desk=desk, hint_id=hint_id)
    return status is not None and 200 <= status <= 299


# --- desk webhook wake (#618) ------------------------------------------------

WAKE_HOSTS_DEFAULT = "api2.cursor.sh/automations/webhook/"
# One POST per desk until it connects or this many seconds pass.
WAKE_WINDOW_S = 120.0
WAKE_TIMEOUT_S = 8.0
KEY_MAX = 512
URL_MAX = 512


class WakeRefused(ValueError):
    """A wake input refused before anything is stored. The text never holds the key."""


def wake_hosts() -> list[tuple[str, str]]:
    """(host, path prefix) pairs from the wall's wake_hosts setting (comma list)."""
    try:
        from agent_coord.config import settings

        raw = str(settings().get("wake_hosts") or "")
    except Exception:
        raw = os.environ.get("AGENT_COORD_WAKE_HOSTS") or ""
    raw = raw.strip() or WAKE_HOSTS_DEFAULT
    out: list[tuple[str, str]] = []
    for part in raw.split(","):
        item = part.strip().lower()
        if not item:
            continue
        if "://" in item:
            item = item.split("://", 1)[1]
        host, _, path = item.partition("/")
        if host:
            out.append((host, "/" + path))
    return out


def _allow_text(allow: list[tuple[str, str]]) -> str:
    return ", ".join(h + p for h, p in allow) or "none"


def allow_step(host: str, allow: list[tuple[str, str]]) -> str:
    """The exact host-Admin step that adds HOST/<prefix>/ to wake_hosts (#619).

    Names where this wall reads the setting: the env var when it is set (it wins
    over the file, and the service reads it at start), else the config file
    (read on every join, no restart). Never a real path, never the URL path.
    """
    listed = ",".join(h + p for h, p in allow)
    value = (listed + "," if listed else "") + f"{host}/<webhook path prefix>/"
    if (os.environ.get("AGENT_COORD_WAKE_HOSTS") or "").strip():
        return (
            f"the host Admin sets AGENT_COORD_WAKE_HOSTS={value} in the mill-wall service "
            "environment on the wall host and must restart mill-wall, then this mill join runs again"
        )
    where = (
        "the file named by AGENT_COORD_CONFIG"
        if (os.environ.get("AGENT_COORD_CONFIG") or "").strip()
        else "~/.mill/config.toml of the account mill-wall runs as"
    )
    return (
        f'the host Admin puts the line wake_hosts = "{value}" in {where} on the wall host '
        "(read on the next join, no restart), then this mill join runs again"
    )


def _ip_literal(host: str) -> bool:
    import ipaddress

    h = host.strip("[]")
    try:
        ipaddress.ip_address(h)
        return True
    except ValueError:
        pass
    # Integer, hex and dotted-octal spellings that resolvers still accept as an address.
    import re

    labels = h.split(".")
    return all(re.fullmatch(r"(?i)0x[0-9a-f]+|[0-9]+", lab or "x") for lab in labels)


def _climbs(path: str) -> bool:
    """True when a URL path could leave its prefix: a . or .. segment, a backslash,
    or an encoded slash or backslash, at any depth of percent-encoding."""
    import re
    from urllib.parse import unquote

    p = path
    for _ in range(5):
        if re.search(r"(?i)%(?:2f|5c)", p) or "\\" in p:
            return True
        if any(seg in (".", "..") for seg in p.split("/")):
            return True
        q = unquote(p)
        if q == p:
            return False
        p = q
    return True  # still encoded after five layers: refuse rather than guess


def looks_like_key(text: str) -> bool:
    t = str(text or "").strip()
    return bool(t) and "/" not in t and (
        t.lower().startswith(("bearer ", "authorization", "crsr_")) or (" " not in t and "." not in t and len(t) >= 16)
    )


def check_url(raw: str, *, allow_only: bool = True) -> tuple[str, str]:
    """(url, host) for a wake URL this wall may POST to, or WakeRefused naming the fix.

    https only, no user or password, default port, host and path prefix on the
    wake_hosts allowlist, never an IP literal. The message never repeats the path.
    """
    from urllib.parse import urlsplit

    url = str(raw or "").strip().strip("'\"").strip()
    if not url:
        raise WakeRefused("join: URL required: --webhook-url URL or --webhook-url-file PATH (the routine's webhook URL)")
    if looks_like_key(url):
        raise WakeRefused(
            "join: that looks like the key, not the URL; the URL starts with https://. "
            "Put the key in --webhook-key-file, --webhook-key-env or --webhook-key-stdin"
        )
    if len(url) > URL_MAX or any(ord(ch) <= 32 or ord(ch) > 126 for ch in url):
        raise WakeRefused(f"join: URL must be one line of plain ASCII up to {URL_MAX} characters")
    parts = urlsplit(url)
    scheme = (parts.scheme or "").lower()
    if scheme != "https":
        raise WakeRefused(
            f"join: https only (got {scheme or 'no scheme'}); copy the https:// webhook URL from the routine"
        )
    if parts.username or parts.password or "@" in parts.netloc:
        raise WakeRefused("join: a URL with a user or password is refused; the key goes in --webhook-key-file")
    host = (parts.hostname or "").lower().rstrip(".")
    try:
        port = parts.port
    except ValueError:
        port = -1
    if not host or _ip_literal(host):
        raise WakeRefused("join: the URL must name a host, not an IP address")
    if port not in (None, 443):
        raise WakeRefused("join: the URL must use the default https port")
    if parts.fragment:
        raise WakeRefused("join: drop the #fragment from the URL")
    if _climbs(parts.path or "/"):
        # Before the prefix check: /allowed/prefix/../../elsewhere must not pass as the prefix.
        raise WakeRefused(
            "join: the URL path has a dot segment (. or ..), or an encoded slash, backslash or dot "
            "that hides one; copy the webhook URL from the routine again"
        )
    if not allow_only:
        # The desk side checks the shape; only the wall knows its allowlist.
        return url, host
    allow = wake_hosts()
    path = parts.path or "/"
    if not any(host == h and path.startswith(p) for h, p in allow):
        step = allow_step(host, allow)
        mine = [p for h, p in allow if h == host]
        if mine:
            raise WakeRefused(
                f"join: that path on {host} is not a webhook path this wall allows "
                f"(allowed on {host}: {', '.join(mine)}); copy the webhook URL from the routine again. "
                f"If it is a new webhook path, {step}"
            )
        raise WakeRefused(
            f"join: host {host} is not on this wall's wake allowlist (allowed: {_allow_text(allow)}). "
            f"To allow it, {step}"
        )
    return url, host


def normalize_key(raw: str) -> str:
    """The bare key from what a person copies: the key, Bearer KEY, or a whole header line.

    WakeRefused for an empty value, a URL, or text that is not one plain token.
    """
    import re

    text = str(raw or "").strip().strip("'\"").strip()
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if len(lines) > 1:
        raise WakeRefused("join: the key is one line; put only the key (or its Authorization line) in the file")
    text = lines[0] if lines else ""
    text = re.sub(r"(?i)^(?:authorization|x-automation-key)\s*:\s*", "", text).strip()
    text = re.sub(r"(?i)^bearer(?:\s+|$)", "", text).strip().strip("'\"").strip()
    if not text:
        raise WakeRefused("join: key required: --webhook-key-file PATH, --webhook-key-env NAME or --webhook-key-stdin (the routine's key)")
    if text.lower().startswith(("http://", "https://")):
        raise WakeRefused("join: that is a URL, not the key; the URL goes in --webhook-url or --webhook-url-file")
    if len(text) > KEY_MAX or len(text) < 8 or not re.fullmatch(r"[!-~]+", text):
        raise WakeRefused("join: the key must be one plain token (8 to 512 visible ASCII characters, no spaces)")
    return text


def _addrs(host: str) -> list[str]:
    import socket

    return sorted({str(info[4][0]) for info in socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP)})


def public_host(host: str) -> bool:
    """True when the host resolves and every address is public (no private, loopback, link-local)."""
    import ipaddress

    try:
        got = _addrs(host)
    except Exception:
        return False
    if not got:
        return False
    for a in got:
        try:
            ip = ipaddress.ip_address(a.split("%", 1)[0])
        except ValueError:
            return False
        if not ip.is_global:
            return False
    return True


# The frame keys a receiver's walk reads (client.dispatch public_frame), and no others.
FRAME_KEYS = ("kind", "type", "id", "hint", "detail", "idem")


def wake_body(desk: str, frame: dict[str, Any], *, pending: int, test: bool = False) -> dict[str, Any]:
    """The POST body: the same frame a sitting desk gets on /ws (with its poke key, idem),
    trimmed to the keys the redirector walk reads, plus one wake block. No letter or card text.
    """
    from agent_coord.server.mill_json import stamp_mill

    body: dict[str, Any] = {k: frame[k] for k in FRAME_KEYS if frame.get(k) not in (None, "")}
    if test:
        body = {"kind": "wake-test"}
    body["desk"] = desk
    body["wake"] = {
        "pending": int(pending),
        "window_s": int(WAKE_WINDOW_S),
        "next": (
            "nothing to do: this is the join test"
            if test
            else f"mill connect {desk}: the sync line hands over every waiting hint and letter, "
            "and this desk's routes walk them"
        ),
    }
    return stamp_mill(body)


def _fix_for(status: int | None, err: str, host: str) -> str:
    if status is None:
        return f"could not reach {host} ({err or 'error'}); check the URL and that the routine exists, then run it again"
    if status in (401, 403):
        return f"{host} refused the key ({status}); copy the key from the routine again and re-run mill join with it"
    if status == 404:
        return f"{host} has no webhook at that URL (404); copy the URL from the routine again"
    if 300 <= status <= 399:
        return f"{host} answered with a redirect ({status}); a wake never follows one; use the routine's final URL"
    return f"{host} answered {status}; try again, or check the routine"


def test_fire(url: str, key: str, desk: str) -> dict[str, Any]:
    """One test POST. {ok, status, host, fix?}. Never the URL path or the key."""
    try:
        url, host = check_url(url)
    except WakeRefused as e:
        return {"ok": False, "status": None, "host": "", "fix": str(e)}
    if not public_host(host):
        return {"ok": False, "status": None, "host": host,
                "fix": f"{host} does not resolve to a public address from this wall"}
    status, err = _post_status(url, wake_body(desk, {}, pending=0, test=True),
                               timeout=WAKE_TIMEOUT_S, key=key, desk=desk, hint_id=None)
    ok = status is not None and 200 <= status <= 299
    out: dict[str, Any] = {"ok": ok, "status": status, "host": host}
    if not ok:
        out["fix"] = _fix_for(status, err, host)
    return out


_GATE: dict[str, float] = {}
_GATE_LOCK = threading.Lock()


def _gate_take(desk: str, now: float) -> bool:
    """True when this desk may be POSTed now; then the window starts."""
    with _GATE_LOCK:
        last = _GATE.get(desk)
        if last is not None and now - last < WAKE_WINDOW_S:
            return False
        _GATE[desk] = now
        return True


def _gate_open(desk: str, now: float) -> bool:
    """True when no window is running for this desk. Takes nothing."""
    with _GATE_LOCK:
        last = _GATE.get(desk)
        return last is None or now - last >= WAKE_WINDOW_S


def gate_clear(desk: str) -> None:
    """The desk connected: its sync has the queue, so the next hint may wake it again."""
    with _GATE_LOCK:
        _GATE.pop(str(desk or "").strip(), None)


def _wake_log(desk: str, frame: dict[str, Any], hint_id: int | None, outcome: str) -> None:
    """One line per desk per wake attempt (#625). Never the URL, its host, or the key
    (the same rule as the webhook fail line; mill connect shows the host)."""
    kind = str(frame.get("kind") or "").strip()
    item = f"kind={kind}" if kind and kind != "hint" else f"type={frame.get('type') or 'hint'}"
    ident = hint_id if hint_id is not None else frame.get("id")
    try:
        from agent_coord.server.push import _bc_log

        _bc_log(f"webhook desk={desk} {item} id={ident} wake={outcome}")
    except Exception:
        return


def post_desk(cn, desk: str, frame: dict[str, Any], *, hint_id: int | None = None) -> str:
    """Wake an armed desk that is not sitting. sent | coalesced | error | off.

    coalesced: a wake already went out in this window and the desk has not
    connected since; the item waits in the push queue like every other one.
    Every outcome but off logs one line (#625): sent with the status, coalesced
    or skipped with the reason, fail with the status or error type.
    """
    import time

    from agent_coord.server.records import join as rec_join

    target = rec_join.wake_target(cn, desk)
    if not target:
        return "off"
    url, key = target
    if not _gate_open(desk, time.monotonic()):
        # A wake already went out in this window: skip the checks and the DNS lookup.
        _wake_log(desk, frame, hint_id, "coalesced reason=window")
        return "coalesced"
    try:
        url, host = check_url(url)
    except WakeRefused:
        _wake_log(desk, frame, hint_id, "skipped reason=not-allowed")
        return "error"
    if not public_host(host):
        _wake_log(desk, frame, hint_id, "skipped reason=not-public")
        return "error"
    # The window starts only for a POST that is actually attempted: a refused or
    # unresolvable target takes no gate, so it never blocks the next valid wake.
    # Taken here (not peeked) so two threads racing past the peek send one POST.
    if not _gate_take(desk, time.monotonic()):
        _wake_log(desk, frame, hint_id, "coalesced reason=window")
        return "coalesced"
    from agent_coord.server.records import push as rec_push

    pending = rec_push.pending(cn, desk) + 1
    status, err = _fire(url, wake_body(desk, frame, pending=pending),
                        timeout=WAKE_TIMEOUT_S, key=key, desk=desk, hint_id=hint_id, quiet=True)
    if status is not None and 200 <= status <= 299:
        _wake_log(desk, frame, hint_id, f"sent status={status}")
        return "sent"
    why = f"status={status}" if status is not None else f"err={err or 'Exception'}"
    _wake_log(desk, frame, hint_id, f"fail {why}")
    return "error"
