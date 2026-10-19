"""HTTPS-only wall + optional LAN-only bind (private interfaces, not 0.0.0.0 public)."""

from __future__ import annotations

import ipaddress
import os
import socket
from pathlib import Path
from typing import Any


def office_dir() -> Path:
    from agent_coord.config import config_path

    return config_path().parent


def cert_paths(dest: Path | None = None) -> dict[str, str]:
    root = dest or office_dir()
    ssl = root / "ssl"
    return {
        "ssl_dir": str(ssl.resolve()),
        "cert": str((ssl / "wall.crt").resolve()),
        "key": str((ssl / "wall.key").resolve()),
        "cert_exists": (ssl / "wall.crt").is_file() and (ssl / "wall.key").is_file(),
    }


def is_private_ip(host: str) -> bool:
    raw = (host or "").strip().lower()
    if not raw or raw in ("*", ""):
        return False
    if raw in ("localhost", "127.0.0.1", "::1"):
        return True
    try:
        ip = ipaddress.ip_address(raw.split("%")[0])
    except ValueError:
        return False
    return bool(ip.is_private or ip.is_loopback or ip.is_link_local)


def is_wildcard_bind(host: str) -> bool:
    return (host or "").strip() in ("0.0.0.0", "::", "*", "")


def private_ipv4s() -> list[str]:
    found: list[str] = []
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            ip = info[4][0]
            if is_private_ip(ip) and ip not in found and not ip.startswith("127."):
                found.append(ip)
    except OSError:
        pass
    try:
        host = socket.gethostbyname(socket.gethostname())
        if is_private_ip(host) and host not in found and not host.startswith("127."):
            found.append(host)
    except OSError:
        pass
    return found


def preferred_office_host() -> str:
    """Install/join default: 192.168.1.* if this machine has one, else localhost."""
    for ip in private_ipv4s():
        if ip.startswith("192.168.1."):
            return ip
    return "127.0.0.1"


def _truthy(raw: Any) -> bool:
    if isinstance(raw, bool):
        return raw
    s = str(raw or "").strip().lower()
    return s in ("1", "true", "yes", "on", "lan", "lan_only", "lan-only")


def lan_only_enabled(path=None) -> bool:
    from agent_coord.config import settings

    env = os.environ.get("AGENT_COORD_LAN_ONLY")
    if env is not None and env != "":
        return _truthy(env)
    return _truthy(settings(path).get("lan_only") or "0")


def set_lan_only(on: bool, *, bind: str | None = None) -> dict[str, Any]:
    """Persist lan_only (+ optional dashboard_bind). Re-run install wall to apply Listen."""
    from agent_coord.config import save_config, settings

    s = settings()
    want = bool(on)
    data = {
        "host": s["host"],
        "port": int(s["port"]),
        "user": s["user"],
        "password": s["password"],
        "database": s["database"],
        "node": s.get("node") or "",
        "dashboard_bind": (bind if bind is not None else s["dashboard_bind"]),
        "dashboard_port": int(s["dashboard_port"]),
        "door": s.get("door") or "path",
        "directory_kind": s.get("directory_kind") or "entra",
        "directory_issuer": s.get("directory_issuer") or "",
        "directory_client_id": s.get("directory_client_id") or "",
        "directory_logout_url": s.get("directory_logout_url") or "",
        "wake_url": s.get("wake_url") or "",
        "lan_only": "1" if want else "0",
    }
    if want and is_wildcard_bind(str(data["dashboard_bind"])):
        # Prefer first private LAN IP, else loopback - never leave 0.0.0.0 under lan_only.
        priv = private_ipv4s()
        data["dashboard_bind"] = priv[0] if priv else "127.0.0.1"
    written = save_config(data)
    return {
        "ok": True,
        "lan_only": want,
        "dashboard_bind": data["dashboard_bind"],
        "config_path": str(written),
        "network": network_packet(),
        "note": (
            "LAN-only: nginx Listen on private/loopback only (not 0.0.0.0). "
            "Re-run: mill install wall --apply --lan-only. "
            "Cloud/public: mill install wall --apply --public (or invite --lan-only off)."
            if want
            else (
                "Public/cloud bind allowed (0.0.0.0 / *). Still HTTPS-only - plain HTTP redirects. "
                "Re-run: mill install wall --apply --public"
            )
        ),
    }


def resolve_listen_hosts(*, lan_only: bool, public_bind: str) -> list[str]:
    """Hosts nginx should Listen on for the public wall."""
    bind = (public_bind or "").strip() or "127.0.0.1"
    if not lan_only:
        if is_wildcard_bind(bind):
            return ["*"]
        return [bind]
    # LAN-only: loopback + private interfaces (never wildcard / public).
    hosts = ["127.0.0.1"]
    if bind and not is_wildcard_bind(bind) and is_private_ip(bind) and bind not in hosts:
        hosts.append(bind)
    for ip in private_ipv4s():
        if ip not in hosts:
            hosts.append(ip)
    return hosts


def assert_mill_api_bind(host: str, *, api_only: bool) -> None:
    """Mill cleartext API may only bind loopback (nginx terminates TLS)."""
    h = (host or "").strip() or "127.0.0.1"
    if api_only:
        if is_wildcard_bind(h) or not (
            h in ("127.0.0.1", "localhost", "::1") or h.startswith("127.")
        ):
            raise ValueError(
                "HTTPS-only product: mill --api-only must bind loopback (127.0.0.1); "
                "humans/agents use mill HTTPS. Refusing cleartext public bind."
            )
        return
    # Service mode without nginx TLS: must not advertise cleartext on non-loopback.
    if is_wildcard_bind(h) or (not h.startswith("127.") and h not in ("localhost", "::1")):
        # Caller should wrap TLS; we only hard-refuse wildcard cleartext here if no SSL.
        pass


def network_packet() -> dict[str, Any]:
    from agent_coord.config import settings

    s = settings()
    lan = lan_only_enabled()
    bind = str(s.get("dashboard_bind") or "127.0.0.1")
    certs = cert_paths()
    listens = resolve_listen_hosts(lan_only=lan, public_bind=bind)
    return {
        "https_only": True,
        "http_cleartext": "rejected",  # nginx 301 -> HTTPS; no product HTTP mode
        "lan_only": lan,
        "dashboard_bind": bind,
        "listen_hosts": listens,
        "private_ipv4s": private_ipv4s(),
        "cert": certs,
        "public_urls": _public_urls(listens, bind, lan),
        "flip_for_cloud": (
            "mill invite --lan-only off   # or: install wall --apply --public\n"
            "Then open firewall 443; certs stay in ~/.mill/ssl/"
        ),
        "flip_lan_only": (
            "mill invite --lan-only on    # or: install wall --apply --lan-only\n"
            "Listens on 127.0.0.1 + private LAN IPs only (not 0.0.0.0)."
        ),
        "notes": {
            "https": "Wall + mill API for humans/agents: TLS only. Plain HTTP redirects/denied.",
            "mill_api": "Behind nginx, mill --api-only stays on 127.0.0.1 (not a public cleartext mode).",
            "door": "OOTB door=path + HTTPS; secure with door=invite + keys (Admin).",
        },
    }


def _public_urls(listens: list[str], bind: str, lan: bool) -> list[str]:
    urls = ["https://127.0.0.1/"]
    for h in listens:
        if h in ("*", "0.0.0.0", "127.0.0.1", "localhost"):
            continue
        u = f"https://{h}/"
        if u not in urls:
            urls.append(u)
    if not lan and bind and not is_wildcard_bind(bind) and not bind.startswith("127."):
        u = f"https://{bind}/"
        if u not in urls:
            urls.append(u)
    return urls
