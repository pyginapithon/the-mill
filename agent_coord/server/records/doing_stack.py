"""join.doing is a stack. Newest entry is first.

The separator is `` | ``. ``\\`` and ``|`` inside an entry are escaped, so a
pipe in the text is not a split. The column is VARCHAR(512). A push that does
not fit drops the oldest entries, then cuts the newest so the stored text fits.

Only the desk writes it (#635). A command that does no other write bumps the seat
and leaves the text alone, so the stack never holds command names. A desk push
also drops the join placeholders and an older copy of the same text.
"""

from __future__ import annotations

LIMIT = 512
SEP = " | "

# Commands that write nothing else: each bumps the seat (join.updated) instead.
BUMP_COMMANDS = frozenset(
    {
        "todo",
        "session",
        "mail-thread",
        "trail",
        "member",
        "trust",
        "invite",
        "move",
        "prune",
        "detach",
        "label-remove",
        "add",
        "remove",
    }
)
# What join writes until the desk says what it is doing.
PLACEHOLDERS = frozenset({"present", "invited"})


def push(stored: str, text: str, *, limit: int = LIMIT) -> str:
    piece = (text or "").replace("\x00", "").strip()
    if not piece:
        return stored or ""
    drop = BUMP_COMMANDS | PLACEHOLDERS | {piece}
    parts = [p for p in split(stored or "") if p not in drop]
    parts.insert(0, piece)
    return _encode(parts, limit)


def clean(stored: str, *, limit: int = LIMIT) -> str:
    """The stack without command names left by walls before #635."""
    parts = split(stored or "")
    kept = [p for p in parts if p not in BUMP_COMMANDS]
    if kept == parts:
        return stored or ""
    return _encode(kept, limit)


def split(stored: str) -> list[str]:
    if not stored:
        return []
    return [_unescape(part) for part in _split_encoded(stored)]


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("|", "\\|")


def _unescape(text: str) -> str:
    out: list[str] = []
    i = 0
    while i < len(text):
        if text[i] == "\\" and i + 1 < len(text):
            out.append(text[i + 1])
            i += 2
            continue
        out.append(text[i])
        i += 1
    return "".join(out)


def _split_encoded(stored: str) -> list[str]:
    parts: list[str] = []
    buf: list[str] = []
    i = 0
    n = len(stored)
    while i < n:
        if stored.startswith(SEP, i) and _pipe_is_separator(stored, i + 1):
            parts.append("".join(buf))
            buf = []
            i += len(SEP)
            continue
        buf.append(stored[i])
        i += 1
    parts.append("".join(buf))
    return parts


def _pipe_is_separator(stored: str, pipe: int) -> bool:
    slashes = 0
    j = pipe - 1
    while j >= 0 and stored[j] == "\\":
        slashes += 1
        j -= 1
    return slashes % 2 == 0


def _encode(parts: list[str], limit: int) -> str:
    kept = list(parts)
    while kept:
        if len(kept) == 1:
            return _fit_one(kept[0], limit)
        encoded = SEP.join(_escape(part) for part in kept)
        if len(encoded) <= limit:
            return encoded
        kept.pop()
    return ""


def _fit_one(text: str, limit: int) -> str:
    if limit < 1:
        return ""
    if len(_escape(text)) <= limit:
        return _escape(text)
    lo, hi = 0, len(text)
    best = ""
    while lo <= hi:
        mid = (lo + hi) // 2
        encoded = _escape(text[:mid])
        if len(encoded) <= limit:
            best = encoded
            lo = mid + 1
        else:
            hi = mid - 1
    return best
