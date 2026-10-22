# -*- coding: utf-8 -*-
"""Rough human Wall ACL by IP/CIDR. Not desk identity. Empty list = allow all."""
from __future__ import annotations

import ipaddress
import os
from pathlib import Path


def allow_path() -> Path:
    from agent_coord.client.tokens import mill_home

    return mill_home() / "wall-allow.txt"


def load_allow() -> list[str]:
    raw = (os.environ.get("AGENT_COORD_WALL_ALLOW") or "").strip()
    if raw:
        return [p.strip() for p in raw.replace(";", ",").split(",") if p.strip()]
    parts: list[str] = []
    p = allow_path()
    if p.is_file():
        for line in p.read_text(encoding="utf-8").splitlines():
            s = line.split("#", 1)[0].strip()
            if s:
                parts.append(s)
    return parts


def client_ip(peer: str, forwarded: str = "") -> str:
    peer = (peer or "").strip() or "127.0.0.1"
    fwd = (forwarded or "").split(",")[0].strip()
    try:
        pip = ipaddress.ip_address(peer.split("%")[0])
    except ValueError:
        pip = None
    if fwd and pip is not None and (pip.is_loopback or pip.is_private):
        return fwd
    return peer


_DEFAULT_PROXIES = ("127.0.0.0/8", "::1")


def trusted_proxies() -> list[str]:
    """Proxies whose X-Forwarded-For door=ip reads. Default: this host's loopback
    (the installed nginx edge). AGENT_COORD_TRUSTED_PROXIES (IP or CIDR, comma
    separated) replaces the default; set it to `none` to trust no proxy."""
    raw = (os.environ.get("AGENT_COORD_TRUSTED_PROXIES") or "").strip()
    if not raw:
        return list(_DEFAULT_PROXIES)
    if raw.lower() == "none":
        return []
    return [p.strip() for p in raw.replace(";", ",").split(",") if p.strip()]


def _in_rules(ip: str, rules: list[str]) -> bool:
    try:
        addr = ipaddress.ip_address((ip or "").split("%")[0].strip())
    except ValueError:
        return False
    for rule in rules:
        try:
            if "/" in rule:
                if addr in ipaddress.ip_network(rule, strict=False):
                    return True
            elif addr == ipaddress.ip_address(rule):
                return True
        except ValueError:
            continue
    return False


def door_client(peer: str, forwarded: str = "") -> tuple[str, bool]:
    """door=ip client address and whether it came from X-Forwarded-For.

    The header is read only when the TCP peer is a trusted proxy (#651). Then
    the hops are read right to left (the proxy appends the address it saw) and
    the first hop that is not a trusted proxy is the client; a spoofed left
    entry is never reached. When every hop is a proxy the leftmost is used,
    still marked forwarded, so allowed() never treats it as this machine.
    """
    peer = (peer or "").strip() or "127.0.0.1"
    proxies = trusted_proxies()
    hops = [h.strip() for h in (forwarded or "").split(",") if h.strip()]
    if not hops or not _in_rules(peer, proxies):
        return peer, False
    for hop in reversed(hops):
        if not _in_rules(hop, proxies):
            return hop[:64], True
    return hops[0][:64], True


def is_loopback(ip: str) -> bool:
    try:
        return ipaddress.ip_address((ip or "").split("%")[0]).is_loopback
    except ValueError:
        return (ip or "").strip().lower() in ("localhost", "")


def workstation_ip(peer: str) -> str:
    """LAN address of the machine that dialed mill-wall. Never 127.0.0.1 or ::1.

    A remote desk's TCP peer is already that workstation. A desk on this host
    that dialed loopback gets this host's outbound IPv4 instead.
    """
    ip = (peer or "").split("%")[0].strip()
    if ip and not is_loopback(ip) and ip not in ("0.0.0.0", "::"):
        return ip[:45]
    import socket

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # RFC 5737. connect() only selects the outbound interface.
        sock.connect(("192.0.2.1", 9))
        got = str(sock.getsockname()[0] or "")
    except OSError:
        return ""
    finally:
        sock.close()
    if not got or is_loopback(got):
        return ""
    return got[:45]


def allowed(
    ip: str,
    rules: list[str] | None = None,
    *,
    empty_open: bool = True,
    forwarded: bool = False,
) -> bool:
    """empty_open=True: no rules means anyone (human Wall). False: mill host loopback only (door=ip).

    forwarded=True: ip came from X-Forwarded-For, so a loopback value is not
    this machine and must be on the allow list like any other address (#651).
    """
    if is_loopback(ip) and not forwarded:
        return True
    rules = load_allow() if rules is None else rules
    if not rules:
        return bool(empty_open)
    return _in_rules(ip, rules)


def is_mill_verb(path: str) -> bool:
    from agent_coord.client.outbound import is_mill_verb_path

    return is_mill_verb_path(path)
