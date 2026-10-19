"""Cold-desk UX: inbox --help steers room catch-up to mail-thread (#79)."""
from __future__ import annotations

import io
import sys


def _help(argv: list[str]) -> str:
    import agent_coord.__main__ as m

    buf = io.StringIO()
    old_out, old_err, old_argv = sys.stdout, sys.stderr, sys.argv
    try:
        sys.stdout = buf
        sys.stderr = buf
        sys.argv = argv
        try:
            m.main()
        except SystemExit as e:
            assert e.code in (0, None)
        return buf.getvalue()
    finally:
        sys.stdout, sys.stderr, sys.argv = old_out, old_err, old_argv


def test_inbox_help_steers_room_catchup_to_mail_thread():
    text = _help(["mill", "inbox", "--help"])
    assert "mail-thread" in text
    assert "Not room catch-up" in text or "not room" in text.lower()
    assert "--no-mark" not in text
    assert "--after" not in text
    text.encode("cp1252")


def test_mail_thread_help_names_room_catchup():
    text = _help(["mill", "mail-thread", "--help"])
    assert "room catch-up" in text.lower() or "catch-up" in text.lower()
    assert "--after" in text
    text.encode("cp1252")
