"""Mail dst/src filter key helpers (purge-mail keyed path)."""
from __future__ import annotations

from .constants import DEAD_LETTER_DST


def flatten_mail_keys(vals: list[str] | tuple[str, ...] | str | None) -> list[str]:
    """CLI/API: repeatable args and/or comma lists -> ordered unique keys."""
    if vals is None:
        return []
    if isinstance(vals, str):
        vals = [vals]
    out: list[str] = []
    seen: set[str] = set()
    for raw in vals:
        for part in str(raw or "").split(","):
            tok = part.strip()
            if not tok or tok in seen:
                continue
            seen.add(tok)
            out.append(tok)
    return out


def expand_mail_filter_keys(keys: list[str] | None) -> set[str]:
    """Match set for dst/src filters: the stored name, *, and the dead-letter box."""
    from agent_coord.helpers.ident import slug

    s: set[str] = set()
    for tok in flatten_mail_keys(keys):
        if tok == "*" or tok == DEAD_LETTER_DST:
            s.add(tok)
            continue
        bare = slug(tok)
        if bare:
            s.add(bare)
    return s
