# -*- coding: utf-8 -*-
"""#770: the Wall glass sends no write request for a human.

Every fetch in wall_ui is a GET, except the admin invite surface (its own
decision) and the glance keypad tap (an in-memory session, no book write).
"""
from __future__ import annotations

import re

from agent_coord.web.wall_logic.packs import wall_ui_root

ROOT = wall_ui_root()

ALLOWED_WRITE_URLS = {
    "/api/admin/invites",
    "/api/v1/glance/tap",
}
GONE_ENDPOINTS = ("/api/desk", "/api/v1/issues", "/api/issues", "/api/v1/collect", "/api/collect")


def _js_files():
    return sorted(p for p in ROOT.rglob("*.js") if "node_modules" not in p.parts)


def _fetch_calls(src: str):
    """Yield (url_literal_or_None, args_text) for each fetch( call."""
    for m in re.finditer(r"\bfetch\(", src):
        i = m.end()
        depth = 1
        j = i
        quote = ""
        while j < len(src) and depth:
            ch = src[j]
            if quote:
                if ch == "\\":
                    j += 2
                    continue
                if ch == quote:
                    quote = ""
            elif ch in "\"'`":
                quote = ch
            elif ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            j += 1
        args = src[i : j - 1]
        lit = re.match(r'\s*["\']([^"\'?]+)', args)
        yield (lit.group(1) if lit else None), args


def test_wall_ui_fetch_writes_only_on_allowed_surfaces():
    bad = []
    seen = 0
    for path in _js_files():
        src = path.read_text(encoding="utf-8")
        for url, args in _fetch_calls(src):
            seen += 1
            meth = re.search(r"\bmethod\s*:\s*([^,}\n]+)", args)
            if not meth:
                continue
            val = meth.group(1).strip()
            if val in ('"GET"', "'GET'"):
                continue
            if url in ALLOWED_WRITE_URLS:
                continue
            bad.append(f"{path.relative_to(ROOT)}: {url or '?'} method {val}")
    assert seen > 10
    assert not bad, bad


def test_wall_ui_names_no_human_write_endpoint():
    hits = []
    for path in _js_files():
        src = path.read_text(encoding="utf-8")
        for ep in GONE_ENDPOINTS:
            if re.search(re.escape(ep) + r"(?![\w/-])", src):
                hits.append(f"{path.relative_to(ROOT)}: {ep}")
    assert not hits, hits


def test_wall_ui_has_no_beacon_or_form_post():
    for path in list(_js_files()) + sorted(ROOT.rglob("*.html")):
        src = path.read_text(encoding="utf-8")
        assert "sendBeacon" not in src, path
        assert "XMLHttpRequest" not in src, path
        assert not re.search(r'<form[^>]*method=["\']?post', src, re.I), path
