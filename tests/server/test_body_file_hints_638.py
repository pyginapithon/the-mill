"""#638: refusal hints and docs name the shipped form, --body-file PATH (F79)."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STALE = re.compile(r"mill (?:reply|send)\b[^\n\"`|]*<body>")


def _hits(paths) -> list[str]:
    out = []
    for p in paths:
        for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if STALE.search(line):
                out.append(f"{p.relative_to(ROOT)}:{n}")
    return out


def test_no_source_hint_names_a_positional_body() -> None:
    assert _hits(sorted((ROOT / "agent_coord").rglob("*.py"))) == []


def test_no_doc_names_a_positional_body() -> None:
    assert _hits(sorted((ROOT / "docs").rglob("*.md"))) == []
