# -*- coding: utf-8 -*-
"""#716: at phone width MAIL Rooms stacks and the collapsed rail keeps roster names.

The glass has no browser in CI, so this test resolves the cascade for the few
elements that matter: it reads the real mail.css and board.css, keeps the rules a
400 px or 1024 px viewport would apply, matches them against each pane state, and
picks the winner by specificity and source order, the way a browser does.
"""
from __future__ import annotations

import re

from agent_coord.web.wall_logic.packs import wall_ui_root

DEFAULT = wall_ui_root() / "default"
SHEETS = ("board.css", "mail/mail.css")  # board.css loads first; mail.css is lazy, after it


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


def _mail(state: str, child: str, tag: str = "aside") -> list[dict]:
    root = _el("div", "mail-browser", "body mail mail-browser " + state, data_mail_view="rooms")
    return [_el("body"), root, _el(tag, child, "mail-col")]


def _rail(on: bool) -> list[dict]:
    row = _el("button", "", "rail-row" + (" on" if on else ""), data_ico="project", data_kind="project")
    return [_el("body", "", "rail-narrow"), _el("aside", "rail"), _el("div", "", "rail-book"), row, _el("span", "", "nm")]


def test_rooms_stack_to_one_column_at_phone_width():
    for state in ("", "dst-open", "src-open", "dst-open src-open"):
        root = [_el("body"), _el("div", "mail-browser", "body mail mail-browser " + state, data_mail_view="rooms")]
        assert _value(400, root, "grid-template-columns") == "minmax(0, 1fr)", state
        assert _value(1024, root, "grid-template-columns") != "minmax(0, 1fr)", state


def test_rooms_list_is_on_top_and_scrolls():
    chain = _mail("", "mail-dst-col")
    assert _value(400, chain, "grid-area") == "rooms"
    assert _value(400, chain, "overflow") == "auto"


def test_party_is_folded_until_its_toggle_opens_it():
    assert _value(400, _mail("", "mail-src-col"), "display") == "none"
    assert _value(400, _mail("src-open", "mail-src-col"), "display") != "none"
    assert _value(400, _mail("src-open", "mail-src-col"), "grid-area") == "party"
    toggle = _mail("", "mail-src-toggle", "button")
    assert _value(400, toggle, "position") == "static"
    rooms_toggle = _mail("", "mail-dst-toggle", "button")
    assert _value(400, rooms_toggle, "display") == "none"


def test_desktop_keeps_three_columns_and_party():
    assert _value(1024, _mail("", "mail-src-col"), "display") != "none"


def test_collapsed_rail_shows_roster_names():
    assert _value(400, _rail(False), "display") == "block"
    assert _value(400, _rail(True), "font-weight") == "700"
    assert _value(400, _rail(False), "font-size") == "10px"


def test_long_roster_name_cannot_widen_the_collapsed_rail():
    # A 64-char roster name once grew every rail row to about 316 px inside a 63 px rail.
    row = _rail(False)[:-1]
    name = _rail(False)
    rail = [_el("body", "", "rail-narrow"), _el("aside", "rail")]
    assert _value(400, rail, "grid-template-columns") == "minmax(0, 1fr)"
    assert _value(400, row, "min-width") == "0"
    assert _value(400, row, "max-width") == "100%"
    assert _value(400, name, "min-width") == "0"
    assert _value(400, name, "overflow") == "hidden"
    assert _value(400, name, "text-overflow") == "ellipsis"
    assert _value(400, name, "white-space") == "nowrap"
    assert _value(400, name, "contain") == "inline-size"
