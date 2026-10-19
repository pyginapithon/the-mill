# -*- coding: utf-8 -*-
"""One pack regression for six office weaknesses.

Reads agent_coord/server, agent_coord/web/wall_ui, and agent_coord/server/sql.
Does not read the human door. Does not attack the office.
A hit is file, line, and check name. The baseline lists current hits.
A source line that is not in the baseline fails the pack test.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASELINE = Path(__file__).with_name("pack_security_baseline.txt")

_PY_SCOPE = ROOT / "agent_coord" / "server"
_SQL_SCOPE = _PY_SCOPE / "sql"
_UI_SCOPE = ROOT / "agent_coord" / "web" / "wall_ui"
_DOOR = (_PY_SCOPE / "admin" / "door.py").resolve()

_REQ = re.compile(
    r"\b(body|args|payload|query|form|request|field|note|detail)\b"
)
_WALL = re.compile(r"\b(body|detail|note)\b")
_LOG_CALL = re.compile(
    r"\b(?:perf_log|_bc_log|api_log|_log\.(?:info|warning|error|debug|exception)"
    r"|logging\.(?:info|warning|error|debug))\s*\("
)
_SECRET_KW = re.compile(
    r"\b(token|password|bearer|seat)\s*=\s*([^,\n)]+)"
)
_ROUTE = re.compile(r"""['\"](/(?:mill/v1|api/v1)/[^'\"]*)['\"]""")
_PROC = re.compile(
    r"CREATE\s+PROCEDURE\s+`?([A-Za-z0-9_]+)`?",
    re.I,
)
_HANDLER = re.compile(r"^def (_h_[A-Za-z0-9_]+)\((.*)\)\s*(?:->.*)?:", re.M)
_WRITE = re.compile(
    r"\b(?:rec_(?:mail|todo|hold|score)|mill_(?:mail|todo|hold|score)_"
    r"(?:put|insert|upsert|update|delete|create))\b"
)


def _rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def _skip(path: Path) -> bool:
    if path.resolve() == _DOOR:
        return True
    rel = _rel(path)
    if "node_modules" in rel.split("/"):
        return True
    if "/__pycache__/" in ("/" + rel):
        return True
    return False


def _py_files() -> list[Path]:
    out = []
    for path in _PY_SCOPE.rglob("*.py"):
        if _skip(path):
            continue
        out.append(path)
    return out


def _ui_files() -> list[Path]:
    out = []
    if not _UI_SCOPE.is_dir():
        return out
    for path in _UI_SCOPE.rglob("*"):
        if path.suffix.lower() not in {".js", ".html"}:
            continue
        if _skip(path):
            continue
        out.append(path)
    return out


def _sql_files() -> list[Path]:
    out = []
    if not _SQL_SCOPE.is_dir():
        return out
    for path in _SQL_SCOPE.rglob("*.sql"):
        if _skip(path):
            continue
        out.append(path)
    return out


def _call_from(lines: list[str], start: int, opener: str) -> tuple[str, int]:
    """Return the call text starting at the opener, and the last line index."""
    buf = []
    depth = 0
    seen = False
    last = start
    for i in range(start, min(len(lines), start + 12)):
        chunk = lines[i]
        buf.append(chunk)
        last = i
        for ch in chunk:
            if ch == "(":
                depth += 1
                seen = True
            elif ch == ")":
                depth -= 1
        if seen and depth <= 0:
            break
    text = "\n".join(buf)
    at = text.find(opener)
    return (text[at:] if at >= 0 else text), last


def _top_args(call: str) -> list[str]:
    start = call.find("(")
    if start < 0:
        return []
    depth = 0
    buf = []
    cur = []
    for ch in call[start:]:
        if ch == "(":
            depth += 1
            if depth > 1:
                cur.append(ch)
            continue
        if ch == ")":
            depth -= 1
            if depth == 0:
                buf.append("".join(cur).strip())
                break
            cur.append(ch)
            continue
        if ch == "," and depth == 1:
            buf.append("".join(cur).strip())
            cur = []
            continue
        if depth >= 1:
            cur.append(ch)
    return [part for part in buf if part]


def _interpolates_request(expr: str) -> bool:
    text = expr.strip()
    if text[:2] in {"f'", 'f"', "F'", 'F"'}:
        return any(_REQ.search(part) for part in re.findall(r"\{([^{}]*)\}", text))
    if "%" in text and _REQ.search(text):
        return True
    return False


def sql_injection_hits(path: str, lines: list[str]) -> list[tuple[int, str, str]]:
    hits = []
    i = 0
    while i < len(lines):
        line = lines[i]
        opener = ".execute(" if ".execute(" in line else ""
        if ".callproc(" in line:
            opener = ".callproc("
        if not opener:
            i += 1
            continue
        call, last = _call_from(lines, i, opener)
        args = _top_args(call)
        if args and _interpolates_request(args[0]):
            hits.append((i + 1, "sql-injection", lines[i].strip()))
        i = last + 1
    return hits


def authz_hits(path: str, text: str) -> list[tuple[int, str, str]]:
    if not path.endswith("api/mill/rpc.py"):
        return []
    hits = []
    matches = list(_HANDLER.finditer(text))
    for n, match in enumerate(matches):
        sig = match.group(2)
        start = match.end()
        end = matches[n + 1].start() if n + 1 < len(matches) else len(text)
        body = text[start:end]
        if not _WRITE.search(body):
            continue
        if "owner" in sig:
            continue
        if re.search(r"\b(admin|bearer|is_admin|_require)\b", body, re.I):
            continue
        line_no = text[: match.start()].count("\n") + 1
        hits.append((line_no, "missing-authorization", match.group(0).strip()))
    return hits


def _auth_gate_line(lines: list[str]) -> int | None:
    for i, line in enumerate(lines, start=1):
        if "Authorization" in line or "PRIVATE-TOKEN" in line:
            return i
    return None


def authn_hits(path: str, lines: list[str]) -> list[tuple[int, str, str]]:
    """A path == route, or a member of path in (...), before the auth gate."""
    gate = _auth_gate_line(lines)
    hits = []
    in_tuple = False
    for i, line in enumerate(lines, start=1):
        if re.search(r"\bpath\s+in\s*\(", line):
            in_tuple = True
        direct = re.search(r"\bpath\s*==", line) is not None
        if direct or in_tuple:
            for route in _ROUTE.findall(line):
                if "version" in route:
                    continue
                if gate is not None and i >= gate:
                    continue
                hits.append((i, "missing-authentication", line.strip()))
                break
        if in_tuple and ")" in line:
            in_tuple = False
    return hits


def secret_hits(path: str, lines: list[str]) -> list[tuple[int, str, str]]:
    hits = []
    i = 0
    while i < len(lines):
        if not _LOG_CALL.search(lines[i]):
            i += 1
            continue
        call, last = _call_from(lines, i, "(")
        blob = "\n".join(lines[i : last + 1])
        if "bad token" in blob:
            i = last + 1
            continue
        flagged = False
        for match in _SECRET_KW.finditer(blob):
            value = match.group(2).strip()
            if value[:1] in {"'", '"'}:
                continue
            if value[:2] in {"f'", 'f"', "F'", 'F"'}:
                continue
            hits.append((i + 1, "secret-exposure", lines[i].strip()))
            flagged = True
            break
        if not flagged and re.search(
            r"\b(token|password|bearer|seat)\s*=\s*\{", blob
        ):
            hits.append((i + 1, "secret-exposure", lines[i].strip()))
        i = last + 1
    return hits


def _blank_sql_comments(text: str) -> str:
    out = []
    i = 0
    while i < len(text):
        if text.startswith("/*", i):
            end = text.find("*/", i + 2)
            end = len(text) if end < 0 else end + 2
            out.append(re.sub(r"[^\n]", " ", text[i:end]))
            i = end
            continue
        if text.startswith("--", i):
            end = text.find("\n", i)
            end = len(text) if end < 0 else end
            out.append(re.sub(r"[^\n]", " ", text[i:end]))
            i = end
            continue
        out.append(text[i])
        i += 1
    return "".join(out)


def unbounded_hits(path: str, text: str) -> list[tuple[int, str, str]]:
    blank = _blank_sql_comments(text)
    hits = []
    procs = list(_PROC.finditer(blank))
    for n, proc in enumerate(procs):
        name = proc.group(1)
        if not re.search(r"_(list|select)$", name, re.I):
            continue
        start = proc.end()
        end = procs[n + 1].start() if n + 1 < len(procs) else len(blank)
        body = blank[start:end]
        depth = 0
        i = 0
        while i < len(body):
            ch = body[i]
            if ch == "(":
                depth += 1
                i += 1
                continue
            if ch == ")":
                depth = max(0, depth - 1)
                i += 1
                continue
            if depth == 0 and body[i : i + 6].upper() == "SELECT" and (
                i == 0 or not body[i - 1].isalnum()
            ):
                j = i
                d = 0
                while j < len(body):
                    if body[j] == "(":
                        d += 1
                    elif body[j] == ")":
                        d = max(0, d - 1)
                    elif body[j] == ";" and d == 0:
                        break
                    j += 1
                stmt = body[i:j]
                head = re.split(r"\bFROM\b", stmt, maxsplit=1, flags=re.I)[0]
                if re.search(r"\bINTO\b", head, re.I):
                    i = j + 1
                    continue
                if not re.search(r"(?i)(?:^|\s)LIMIT(?:\s|$)", _depth0(stmt)):
                    line_no = blank[: start + i].count("\n") + 1
                    src = text.splitlines()[line_no - 1].strip()
                    hits.append((line_no, "unbounded-read", src))
                i = j + 1
                continue
            i += 1
    return hits


def _depth0(stmt: str) -> str:
    out = []
    depth = 0
    for ch in stmt:
        if ch == "(":
            depth += 1
            continue
        if ch == ")":
            depth = max(0, depth - 1)
            continue
        if depth == 0:
            out.append(ch)
    return "".join(out)


def _code_outside_strings(line: str) -> str:
    return re.sub(
        r"""(`(?:\\`|[^`])*`|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')""",
        '""',
        line,
    )


def _html_argument(line: str) -> str:
    marked = _code_outside_strings(line)
    assign = re.search(r"\.innerHTML\s*=\s*(.*)$", marked)
    if assign:
        return assign.group(1)
    inserted = re.search(r"insertAdjacentHTML\s*\([^,]*,\s*(.*)\)", marked)
    if inserted:
        return inserted.group(1)
    return ""


def html_hits(path: str, lines: list[str]) -> list[tuple[int, str, str]]:
    hits = []
    for i, line in enumerate(lines, start=1):
        if "document.write" in line and re.search(
            r"stylesheet|<link|<style", line, re.I
        ):
            continue
        if "innerHTML" not in line and "insertAdjacentHTML" not in line:
            continue
        if "esc(" in line:
            continue
        if not _WALL.search(_html_argument(line)):
            continue
        hits.append((i, "wall-html", line.strip()))
    return hits


def scan_text(path: str, text: str) -> list[tuple[int, str, str]]:
    lines = text.splitlines()
    hits: list[tuple[int, str, str]] = []
    suffix = path.replace("\\", "/")
    if suffix.endswith(".py"):
        hits.extend(sql_injection_hits(suffix, lines))
        hits.extend(authz_hits(suffix, text))
        hits.extend(authn_hits(suffix, lines))
        hits.extend(secret_hits(suffix, lines))
    elif suffix.endswith(".sql"):
        hits.extend(unbounded_hits(suffix, text))
    elif suffix.endswith(".js") or suffix.endswith(".html"):
        hits.extend(html_hits(suffix, lines))
    return hits


def _key(path: str, check: str, source: str) -> str:
    collapsed = " ".join(source.split())
    return f"{path}|{check}|{collapsed}"


def scan_pack(root: Path | None = None) -> list[tuple[str, int, str, str]]:
    """Hits as (relpath, line, check, source)."""
    rows: list[tuple[str, int, str, str]] = []
    files = _py_files() + _sql_files() + _ui_files()
    for path in files:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = _rel(path)
        for line_no, check, source in scan_text(rel, text):
            rows.append((rel, line_no, check, source))
    rows.sort(key=lambda row: (row[0], row[1], row[2], row[3]))
    return rows


def baseline_keys(text: str) -> list[str]:
    return [line for line in text.splitlines() if line.strip() and not line.startswith("#")]


def test_pack_security_baseline_holds() -> None:
    rows = scan_pack()
    found = [_key(path, check, source) for path, _line, check, source in rows]
    expected = baseline_keys(BASELINE.read_text(encoding="utf-8"))
    missing = sorted(set(found) - set(expected))
    extra = sorted(set(expected) - set(found))
    if not missing and not extra:
        return
    report = []
    by_key = {}
    for path, line_no, check, source in rows:
        by_key.setdefault(_key(path, check, source), f"{path}:{line_no}:{check}")
    for key in missing:
        report.append(by_key.get(key, key))
    detail = "new hits: " + ", ".join(report) if report else "new hits: none"
    if extra:
        detail += f"; baseline only: {len(extra)}"
    raise AssertionError(detail)


def test_pack_security_flags_the_six_shapes() -> None:
    sql = 'cur.execute(f"SELECT {body} FROM t")\ncur.execute(sql, (body,))\n'
    assert any(check == "sql-injection" for _n, check, _s in scan_text("a.py", sql))
    assert sum(1 for _n, check, _s in scan_text("a.py", sql) if check == "sql-injection") == 1

    handler = (
        "def _h_open(c, body, project):\n"
        "    rec_mail.put(c, body)\n"
        "def _h_ok(c, body, project, owner):\n"
        "    rec_mail.put(c, body)\n"
    )
    authz = scan_text("agent_coord/server/api/mill/rpc.py", handler)
    assert [row[1] for row in authz] == ["missing-authorization"]

    route = 'if path == "/api/v1/open":\n    return\nauth = headers.get("Authorization")\n'
    assert any(
        check == "missing-authentication" for _n, check, _s in scan_text("m.py", route)
    )
    version = 'if path == "/mill/v1/version":\n    return\n'
    assert scan_text("m.py", version) == []

    secret = 'perf_log("verb", ms, token=tok)\napi_log("bad token desk=%s" % who)\n'
    secrets = [row for row in scan_text("a.py", secret) if row[1] == "secret-exposure"]
    assert len(secrets) == 1

    proc = (
        "CREATE PROCEDURE mill_demo_select()\n"
        "BEGIN\n"
        "  SELECT id FROM mail;\n"
        "END\n"
        "CREATE PROCEDURE mill_capped_select()\n"
        "BEGIN\n"
        "  SELECT id FROM mail LIMIT 500;\n"
        "END\n"
    )
    unbounded = scan_text("sp.sql", proc)
    assert len(unbounded) == 1 and unbounded[0][1] == "unbounded-read"

    wall = (
        "el.innerHTML = note\n"
        "el.innerHTML = esc(note)\n"
        "el.textContent = note\n"
        "document.write('<link rel=\"stylesheet\" href=\"a.css\">')\n"
    )
    html = scan_text("wall.js", wall)
    assert len(html) == 1 and html[0][1] == "wall-html"
