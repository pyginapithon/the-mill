"""Session vendor env helper (Path A extract from coord.py)."""
from __future__ import annotations

import os


def session_vendor() -> str:
    """AGENT_COORD_VENDOR from env (grok/claude/chatgpt/gemini/...). Empty if unset."""
    return (os.environ.get("AGENT_COORD_VENDOR") or "").strip().lower()[:32]
