"""git-changes pretty/pipe helpers."""
from __future__ import annotations

from tools.git_changes import changes as ch


def test_format_pretty_no_color():
    pair = ch.RevPair("a", "b", "a (aaa)", "HEAD (bbb)", "upstream origin/main")
    text = ch.format_pretty(pair, [("M", "x.py")], "1 file changed", color=False)
    assert "git-changes" in text and "x.py" in text


def test_colorize_file_header_counts():
    raw = (
        "diff --git a/x.py b/x.py\n"
        "--- a/x.py\n+++ b/x.py\n"
        "@@ -1 +1,2 @@\n"
        "-old\n+new1\n+new2\n"
    )
    plain = ch.colorize_diff(raw, color=False)
    assert "FILE" in plain and "x.py" in plain
    assert "+2" in plain and "-1" in plain
    assert "diff --git a/x.py b/x.py" in plain
    colored = ch.colorize_diff(raw, color=True)
    assert "\033[7m" in colored and "\033[1;92m" in colored and "\033[31m" in colored


def test_run_changes_names_same_rev():
    code, text = ch.run_changes(old="HEAD", new="HEAD", mode="names", color=False)
    assert code == 0 and text.strip() == ""
