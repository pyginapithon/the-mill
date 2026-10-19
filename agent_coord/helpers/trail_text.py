"""mill trail: plain-text render of a trail result (client side, no SQL).

A trail result is {"root": {...}, "tree": name, "nodes": [...], "truncated": bool}.
Each node: kind, id, depth, state, title, last_note, mark, who, at_pt.
"""
from __future__ import annotations

import re
from typing import Any

LINE_MAX = 120
DEAD_END = "DEAD END"
SOLVED = "SOLVED"
# Leading word, then anything up to a colon, any case (#156).
_DEAD_RE = re.compile(r"^(?:dead-end|dead end)\b[^:\n]*:", re.IGNORECASE)
_SOLVED_RE = re.compile(r"^solved\b[^:\n]*:", re.IGNORECASE)


def clip(text: str, n: int = LINE_MAX) -> str:
    s = " ".join(str(text or "").split())
    if len(s) <= n:
        return s
    return s[: max(1, n - 3)].rstrip() + "..."


def first_line(text: str) -> str:
    for line in str(text or "").splitlines():
        if line.strip():
            return line.strip()
    return ""


def last_line(text: str) -> str:
    for line in reversed(str(text or "").splitlines()):
        if line.strip():
            return line.strip()
    return ""


def mark_of(note: str) -> str:
    """DEAD END / SOLVED when the note leads with that word and a colon (#156)."""
    text = str(note or "").strip()
    if _DEAD_RE.match(text):
        return DEAD_END
    if _SOLVED_RE.match(text):
        return SOLVED
    return ""


def node_line(node: dict[str, Any]) -> str:
    indent = "  " * int(node.get("depth") or 0)
    kind = str(node.get("kind") or "?")
    nid = node.get("id")
    state = str(node.get("state") or "")
    head = f"{indent}{kind} {nid} [{state}]"
    mark = str(node.get("mark") or "")
    if mark:
        head += f" [{mark}]"
    title = clip(node.get("title") or "")
    if title:
        head += f" {title}"
    note = clip(node.get("last_note") or "")
    if note and note != title:
        head += f" -- last note: {note}"
    tail = [x for x in (str(node.get("who") or ""), str(node.get("at_pt") or "")) if x]
    if tail:
        head += " (" + ", ".join(tail) + ")"
    return head


def render_label(result: dict[str, Any]) -> str:
    """trail --label: id, type, ord, clipped body or need, created (#199)."""
    label = str(result.get("label") or "")
    rows = list(result.get("rows") or [])
    lines = ["trail --label %s: %s row(s)" % (label, len(rows))]
    hint = str(result.get("hint") or "")
    if hint:
        lines.append(hint)
    for row in rows:
        text = str(row.get("need") or row.get("body") or "")
        lines.append(
            "%s %s ord %s %s %s"
            % (row.get("type"), row.get("id"), row.get("ord"), text, row.get("created") or "")
        )
    if result.get("truncated"):
        lines.append("... truncated at %s row(s)" % len(rows))
    return "\n".join(lines)


def render(result: dict[str, Any]) -> str:
    if "rows" in result and "label" in result:
        return render_label(result)
    nodes = list(result.get("nodes") or [])
    root = result.get("root") or {}
    tree = str(result.get("tree") or "")
    # Reply-opened rooms sit on a hidden (unnamed) tree: say so, not "not on a tree".
    # Older servers lack on_tree; more than one node also means a tree.
    if tree:
        where = f" on {tree}"
    elif result.get("on_tree") or len(nodes) > 1:
        where = " on an unnamed tree"
    else:
        where = " (not on a tree)"
    head = f"trail {root.get('kind', '?')} {root.get('id', '?')}{where}: {len(nodes)} node(s)"
    dead = sum(1 for n in nodes if n.get("mark") == DEAD_END)
    solved = sum(1 for n in nodes if n.get("mark") == SOLVED)
    if dead or solved:
        head += f", {dead} dead end(s), {solved} solved"
    lines = [head] + [node_line(n) for n in nodes]
    if result.get("truncated"):
        lines.append(f"... truncated at {len(nodes)} nodes")
    return "\n".join(lines)
