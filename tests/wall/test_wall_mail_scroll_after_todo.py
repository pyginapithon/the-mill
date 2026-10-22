# -*- coding: utf-8 -*-
"""#772: once the TODO pane has loaded todo.css, MAIL columns still scroll.

todo.css loads on the first TODO visit and stays for the session. Its text-mode rules
used a bare .mail-col, so the MAIL thread column lost overflow-y: auto and Letters
could not scroll. The glass has no browser in CI, so this test resolves the cascade
of the real board.css, mail.css and todo.css (media, specificity, source order) for
the MAIL thread column in each text mode, the way a browser does.
"""
from __future__ import annotations

import re

from agent_coord.web.wall_logic.packs import wall_ui_root

DEFAULT = wall_ui_root() / "default"
SHEETS = ("board.css", "mail/mail.css", "todo/todo.css")  # TODO opened after MAIL: todo.css last


def _rules(width: int) -> list[tuple[str, str, int]]:
    """(selector, declarations, order) for every rule this viewport applies."""
    out: list[tuple[str, str, int]] = []
    order = 0
    for name in SHEETS:
        css = re.sub(r"/\*.*?\*/", "", (DEFAULT / name).read_text(encoding="utf-8"), flags=re.S)
        i = 0
        stack: list[bool] = []
        head = ""
        while i < len(css):
            ch = css[i]
            if ch == "{":
                sel = head.strip()
                head = ""
                if sel.startswith("@media"):
                    m = re.search(r"max-width:\s*(\d+)px", sel)
                    n = re.search(r"min-width:\s*(\d+)px", sel)
                    ok = (not m or width <= int(m.group(1))) and (not n or width >= int(n.group(1)))
                    stack.append(ok)
                elif sel.startswith("@"):
                    stack.append(False)
                else:
                    j = css.index("}", i)
                    if all(stack):
                        for one in sel.split(","):
                            order += 1
                            out.append((" ".join(one.split()), css[i + 1:j], order))
                    i = j
            elif ch == "}":
                if stack:
                    stack.pop()
                head = ""
            else:
                head += ch
            i += 1
    return out


def _spec(sel: str) -> tuple[int, int, int]:
    bits = sel
    a = b = c = 0
    for inner in re.findall(r":not\(([^)]*)\)", bits):
        x, y, z = _spec(inner)
        a, b, c = a + x, b + y, c + z
    bits = re.sub(r":not\([^)]*\)", "", bits)
    bits = re.sub(r"::[a-z-]+", " ", bits)
    a += len(re.findall(r"#[\w-]+", bits))
    b += len(re.findall(r"\.[\w-]+|\[[^\]]*\]|:[\w-]+", bits))
    c += len(re.findall(r"(?:^|[\s>+~])([a-z][\w-]*)", bits))
    return a, b, c


def _matches(sel: str, chain: list[dict]) -> bool:
    """chain: root first, element last; each {tag, id, cls, attrs}. Descendant/child only."""
    parts = re.split(r"\s*(>)\s*|\s+", sel)
    parts = [p for p in parts if p]

    def simple(tok: str, el: dict) -> bool:
        for neg in re.findall(r":not\(([^)]*)\)", tok):
            if simple(neg, el):
                return False
        tok = re.sub(r":not\([^)]*\)", "", tok)
        if "::" in tok:
            return False
        tag = re.match(r"^[a-z][\w-]*", tok)
        if tag and tag.group(0) != el["tag"]:
            return False
        for i in re.findall(r"#([\w-]+)", tok):
            if el.get("id") != i:
                return False
        for k in re.findall(r"\.([\w-]+)", tok):
            if k not in el["cls"]:
                return False
        for k, v in re.findall(r'\[([\w-]+)(?:="([^"]*)")?\]', tok):
            if k not in el["attrs"] or (v and el["attrs"][k] != v):
                return False
        return not re.search(r":(?!not)[\w-]+", tok)

    def walk(pi: int, ei: int, child: bool) -> bool:
        if pi < 0:
            return True
        if parts[pi] == ">":
            return walk(pi - 1, ei, True)
        if child:
            return ei >= 0 and simple(parts[pi], chain[ei]) and walk(pi - 1, ei - 1, False)
        for k in range(ei, -1, -1):
            if simple(parts[pi], chain[k]) and walk(pi - 1, k - 1, False):
                return True
        return False

    last = parts[-1]
    return simple(last, chain[-1]) and walk(len(parts) - 2, len(chain) - 2, False)


def _value(width: int, chain: list[dict], prop: str) -> str:
    best = None
    for sel, decl, order in _rules(width):
        if not _matches(sel, chain):
            continue
        for d in decl.split(";"):
            if ":" not in d:
                continue
            k, v = d.split(":", 1)
            if k.strip() != prop:
                continue
            imp = "!important" in v
            key = (imp, _spec(sel), order)
            if best is None or key > best[0]:
                best = (key, v.replace("!important", "").strip())
    return best[1] if best else ""


def _el(tag: str, id_: str = "", cls: str = "", **attrs: str) -> dict:
    return {"tag": tag, "id": id_, "cls": set(cls.split()), "attrs": {k.replace("_", "-"): v for k, v in attrs.items()}}




def _overflow_y(width: int, chain: list[dict]) -> str:
    """overflow-y from the winning overflow-y or overflow (shorthand: x [y]) declaration."""
    best = None
    for sel, decl, order in _rules(width):
        if not _matches(sel, chain):
            continue
        for d in decl.split(";"):
            if ":" not in d:
                continue
            k, v = d.split(":", 1)
            k = k.strip()
            if k not in ("overflow", "overflow-y"):
                continue
            imp = "!important" in v
            vals = v.replace("!important", "").split()
            y = vals[-1] if k == "overflow" else vals[0]
            key = (imp, _spec(sel), order)
            if best is None or key > best[0]:
                best = (key, y)
    return best[1] if best else "visible"


def _col(mode: str, pane: str, col: str = "mail-msg-col") -> list[dict]:
    return [
        _el("body", "", "", data_text_mode=mode),
        _el("div", pane, "pane on"),
        _el("div", "mail-browser", "body mail mail-browser", data_mail_view="letters"),
        _el("div", "mail-msg-col", "mail-col " + col),
    ]


def test_mail_thread_scrolls_in_every_text_mode_after_todo_loaded():
    for mode in ("wrap", "clip", "overflow"):
        for width in (1280, 1024):
            assert _overflow_y(width, _col(mode, "pane-mail")) == "auto", (mode, width)


def test_todo_text_mode_still_applies_inside_the_todo_pane():
    assert _overflow_y(1280, _col("wrap", "pane-todo")) == "hidden"
    assert _value(1280, _col("wrap", "pane-todo"), "white-space") == "normal"
