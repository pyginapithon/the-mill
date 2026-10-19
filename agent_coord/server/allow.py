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


def allowed(ip: str, rules: list[str] | None = None, *, empty_open: bool = True) -> bool:
    """empty_open=True: no rules means anyone (human Wall). False: mill host loopback only (door=ip)."""
    if is_loopback(ip):
        return True
    rules = load_allow() if rules is None else rules
    if not rules:
        return bool(empty_open)
    try:
        addr = ipaddress.ip_address((ip or "").split("%")[0])
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


def is_mill_verb(path: str) -> bool:
    from agent_coord.client.outbound import is_mill_verb_path

    return is_mill_verb_path(path)
