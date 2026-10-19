"""Help text gaps: --office, inbox catch-up, mail-thread join, send form (#158)."""
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


def _listed_verbs(top: str) -> list[str]:
    names: list[str] = []
    in_pos = False
    for line in top.splitlines():
        if line.startswith("positional arguments:"):
            in_pos = True
            continue
        if in_pos and line and not line[:1].isspace():
            break
        if not in_pos or not line.startswith("    ") or line.startswith("      "):
            continue
        name = line.strip().split()[0]
        if name and name != "VERB" and not name.startswith("-"):
            names.append(name)
    return names


def test_office_is_on_every_listed_help():
    top = _help(["mill", "-h"])
    assert "--office" in top
    verbs = _listed_verbs(top)
    assert "inbox" in verbs
    assert "send" in verbs
    assert "mail-thread" in verbs
    for verb in verbs:
        text = _help(["mill", verb, "-h"])
        assert "--office" in text, verb
        text.encode("cp1252")


def test_inbox_help_points_at_the_branch_cursor():
    text = _help(["mill", "inbox", "-h"])
    assert "mail-thread" in text
    assert "last read" in text
    assert "--room" not in text
    text.encode("cp1252")


def test_mail_thread_help_join_matches_reply_syntax():
    text = _help(["mill", "mail-thread", "-h"])
    flat = " ".join(text.split())
    assert "mill reply <root id> --body-file PATH" in flat
    assert "<body>" not in flat
    text.encode("cp1252")


def test_send_help_shows_the_current_form():
    text = _help(["mill", "send", "-h"])
    assert "--body-file" in text
    assert "--to-desk" in text
    assert "PROJECT SRC DST BODY" not in text
    text.encode("cp1252")
