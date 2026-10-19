"""Idempotency key for one poke. The event, not the attempt or the path.

Hint is type, id, and the watcher desk. A letter is the mail id and the
destination desk. A receipt is the mail id and the sender desk. No table.
"""
from __future__ import annotations

FIELD = "idem"


def hint_key(type: str, id: int, desk: str) -> str:
    return f"hint:{type}:{int(id)}:{str(desk or '').strip()}"


def letter_key(mail_id: int, dest: str) -> str:
    return f"letter:{int(mail_id)}:{str(dest or '').strip()}"


def receipt_key(mail_id: int, sender: str) -> str:
    return f"receipt:{int(mail_id)}:{str(sender or '').strip()}"
