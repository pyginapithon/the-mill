"""Example mill connect HINT program. Replace with mill inbox / mill todo.

stdin: one JSON HINT object. mill connect does not wait.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

raw = sys.stdin.read()
try:
    hint = json.loads(raw or "{}")
except json.JSONDecodeError:
    hint = {"raw": (raw or "")[:200]}
line = json.dumps(hint, default=str)
print("HINT", line, flush=True)
try:
    dest = Path.home() / ".mill" / "session"
    dest.mkdir(parents=True, exist_ok=True)
    desk = str(hint.get("desk") or "unknown").strip() or "unknown"
    path = dest / f"{desk}.hint-spawn.jsonl"
    with path.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")
except OSError:
    pass
