# -*- coding: utf-8 -*-
"""Wall JS: every camelCase name a Wall script reads is declared in some Wall script (#726).

The Wall's classic scripts share one global scope. A lazy paint module
(score/score-paint.js, mail/mail-paint.js and the rest) reads boot.js state by
name, so a rename in boot.js that misses a moved module leaves a name that is
declared nowhere. The browser only finds it as a ReferenceError when that pane
paints. This test finds it at commit time, with no Node.js.

How: strip comments and string text (template ${...} stays), collect every
declared name in all Wall .js files (function, class, parameters, let/const/var,
arrow parameters, catch, window./global. assignments), then check each
camelCase name read outside a property access or an object key. Scope is the
whole Wall, so it catches names declared nowhere, not names used out of scope.
All-lowercase names are not checked (too many short locals); the renames that
cross files here are camelCase.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "agent_coord" / "web" / "wall_ui"
ID = r"[A-Za-z_$][\w$]*"
BROWSER = {
    "cancelAnimationFrame", "clearInterval", "clearTimeout", "decodeURIComponent",
    "encodeURIComponent", "getComputedStyle", "globalThis", "indexedDB", "isFinite",
    "isNaN", "localStorage", "matchMedia", "parseFloat", "parseInt", "queueMicrotask",
    "requestAnimationFrame", "sessionStorage", "setInterval", "setTimeout", "structuredClone",
}
_USE = re.compile(r"(?<![.\w$])([a-z][a-z0-9]*[A-Z][\w$]*)\b(?!\s*:(?!:))")


def _skip_template_expr(src: str, k: int) -> int:
    """Index just past the } closing the ${ that ends at k."""
    depth = 1
    while k < len(src) and depth:
        ch = src[k]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        elif ch == "`":
            close = src.find("`", k + 1)
            k = close if close > 0 else k
        k += 1
    return k


def strip(src: str) -> str:
    """Code with comments, string text and regex literals blanked; ${...} code kept."""
    out: list[str] = []
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        if src.startswith("//", i):
            j = src.find("\n", i)
            i = n if j < 0 else j
            continue
        if src.startswith("/*", i):
            j = src.find("*/", i + 2)
            i = n if j < 0 else j + 2
            out.append(" ")
            continue
        if c in "\"'":
            j = i + 1
            while j < n and src[j] != c and src[j] != "\n":
                j += 2 if src[j] == "\\" else 1
            out.append('""')
            i = j + 1
            continue
        if c == "`":
            j = i + 1
            out.append(" ")
            while j < n and src[j] != "`":
                if src[j] == "\\":
                    j += 2
                    continue
                if src.startswith("${", j):
                    k = _skip_template_expr(src, j + 2)
                    out.append(" " + strip(src[j + 2:k - 1]) + " ")
                    j = k
                    continue
                j += 1
            i = j + 1
            continue
        if c == "/":
            prev = "".join(out[-40:]).rstrip()[-1:]
            if prev == "" or prev in "(,=:[!&|?{};":
                j, in_class = i + 1, False
                while j < n and src[j] != "\n":
                    if src[j] == "\\":
                        j += 2
                        continue
                    if src[j] == "[":
                        in_class = True
                    elif src[j] == "]":
                        in_class = False
                    elif src[j] == "/" and not in_class:
                        break
                    j += 1
                if j < n and src[j] == "/":
                    out.append(" /r/ ")
                    i = j + 1
                    continue
        out.append(c)
        i += 1
    return "".join(out)


def _declarator_names(stmt: str) -> list[str]:
    """Names declared by the text after let/const/var, up to the first ; ."""
    parts, part, depth = [], "", 0
    for ch in stmt:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
            if depth < 0:
                break
        if ch == "," and depth == 0:
            parts.append(part)
            part = ""
            continue
        part += ch
    parts.append(part)
    names = []
    for p in parts:
        m = re.match(r"\s*(" + ID + r")\s*(?:=|$)", p)
        if m:
            names.append(m.group(1))
    return names


def undeclared(root: Path = ROOT) -> dict[str, list[str]]:
    declared: set[str] = set()
    uses: dict[str, set[str]] = {}
    for f in sorted(root.rglob("*.js")):
        s = strip(f.read_text(encoding="utf-8"))
        declared.update(re.findall(r"\b(?:function\*?|class)\s+(" + ID + ")", s))
        for m in re.finditer(r"\bfunction\*?\s*(?:" + ID + r")?\s*\(([^)]*)\)", s):
            declared.update(re.findall(ID, m.group(1)))
        for m in re.finditer(r"\b(?:let|const|var)\s+([^;=]+?)(?==|;|\bof\b|\bin\b)", s):
            declared.update(re.findall(ID, m.group(1)))
        for m in re.finditer(r"\b(?:let|const|var)\s+([^;]*)", s):
            declared.update(_declarator_names(m.group(1)))
        for m in re.finditer(r"\(([^()]*)\)\s*=>", s):
            declared.update(re.findall(ID, m.group(1)))
        declared.update(re.findall(r"(" + ID + r")\s*=>", s))
        declared.update(re.findall(r"\bcatch\s*\(\s*(" + ID + ")", s))
        declared.update(re.findall(r"\b(?:window|globalThis|self|global|root|g)\.(" + ID + r")\s*=", s))
        for m in _USE.finditer(s):
            uses.setdefault(m.group(1), set()).add(f.relative_to(root).as_posix())
    return {k: sorted(v) for k, v in sorted(uses.items()) if k not in declared and k not in BROWSER}


def test_wall_js_reads_no_undeclared_name():
    assert sorted(ROOT.rglob("*.js")), ROOT
    missing = undeclared()
    assert not missing, (
        "Wall JS reads names no Wall script declares (a rename leftover is a ReferenceError "
        "when that pane paints): " + "; ".join(k + " in " + ", ".join(v) for k, v in missing.items())
    )


def test_check_finds_a_rename_leftover(tmp_path):
    (tmp_path / "boot.js").write_text(
        'let scoreSelectedCommand = "";\nfunction paintIt() { return scoreSelectedCommand; }\n'
    )
    (tmp_path / "paint.js").write_text(
        "function paintMore() { if (!scoreSelectedVerb) return `${scoreSelectedVerb}`; }\n"
        "const note = 'scoreSelectedOther in a string is fine'; // so is scoreSelectedOld here\n"
    )
    assert undeclared(tmp_path) == {"scoreSelectedVerb": ["paint.js"]}
