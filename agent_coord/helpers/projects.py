"""Up-front project check. Unknown, retired, and empty are a plain refusal."""
from __future__ import annotations


def project_refusal(verb: str, project: str, names: list[str]) -> str | None:
    """None when project is a live name. Otherwise the refusal sentence.

    The sentence is `verb: no such project X; projects: a, b`.
    A blank project omits X. names are the live projects, already ordered.
    """
    who = str(project or "").strip()
    live: list[str] = []
    seen: set[str] = set()
    for raw in names or []:
        nm = str(raw or "").strip()
        if not nm or nm in seen:
            continue
        seen.add(nm)
        live.append(nm)
    if who and who in seen:
        return None
    shown = ", ".join(live) if live else "(none)"
    if who:
        return "%s: no such project %s; projects: %s" % (verb, who, shown)
    return "%s: no such project; projects: %s" % (verb, shown)
