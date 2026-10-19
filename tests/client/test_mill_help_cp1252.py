"""CLI help must be printable on stock Windows cp1252 consoles."""
from __future__ import annotations

import io
import sys


def test_mill_help_encodes_as_cp1252():
    import agent_coord.__main__ as m

    buf = io.BytesIO()
    wrapped = io.TextIOWrapper(buf, encoding="cp1252", errors="strict", newline="\n")
    old_out, old_err, old_argv = sys.stdout, sys.stderr, sys.argv
    try:
        sys.stdout = wrapped
        sys.stderr = wrapped
        sys.argv = ["mill", "--help"]
        try:
            m.main()
        except SystemExit as e:
            assert e.code in (0, None)
        wrapped.flush()
        raw = buf.getvalue()
        assert raw, "expected --help output"
        raw.decode("cp1252")  # round-trip
        assert b"\xe2\x86\x92" not in raw  # UTF-8 bytes for -> must not appear
    finally:
        try:
            wrapped.detach()
        except Exception:
            pass
        sys.stdout, sys.stderr, sys.argv = old_out, old_err, old_argv


def test_main_help_strings_are_cp1252():
    from pathlib import Path

    text = Path(m_path()).read_text(encoding="utf-8")
    for i, line in enumerate(text.splitlines(), 1):
        if "help=" not in line and "add_parser(" not in line:
            continue
        try:
            line.encode("cp1252")
        except UnicodeEncodeError as exc:
            raise AssertionError(f"agent_coord/__main__.py:{i} not cp1252: {exc}") from exc


def m_path():
    import agent_coord.__main__ as m

    return m.__file__
