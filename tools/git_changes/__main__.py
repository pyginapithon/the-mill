"""python -m tools.git_changes  OR  tools/bin/git-changes"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# allow running without install: put repo root on path
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT.parent) not in sys.path:
    # parents: git_changes -> tools -> repo
    pass
_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from tools.git_changes.changes import _page, run_changes, stdout_is_tty  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="git-changes",
        description="Pretty changes between two git versions (default: last version -> HEAD). "
        "TTY: pretty table. Piped/redirected: path list (no color).",
    )
    p.add_argument("--from", dest="changes_from", default="", help="old rev/tag (default: last version)")
    p.add_argument("--to", dest="changes_to", default="HEAD", help="new rev (default: HEAD)")
    p.add_argument("--pretty", action="store_true", help="force pretty table (default on TTY)")
    p.add_argument("--names", action="store_true", help="paths only (default when stdout is piped)")
    p.add_argument("--stat", action="store_true", help="shortstat only")
    p.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="show line diffs (paged on TTY; same as --patch)",
    )
    p.add_argument("--patch", "-p", action="store_true", help="same as --verbose")
    p.add_argument("--no-color", action="store_true", help="disable ANSI (also auto when not a TTY)")
    p.add_argument("paths", nargs="*", help="optional path filters")
    args = p.parse_args(argv)

    mode = "pretty"
    if args.patch or args.verbose:
        mode = "patch"
    elif args.names:
        mode = "names"
    elif args.stat:
        mode = "stat"
    elif args.pretty:
        mode = "pretty"
    elif not stdout_is_tty():
        mode = "names"

    color = False if args.no_color or not stdout_is_tty() else True
    code, text = run_changes(
        old=args.changes_from or None,
        new=args.changes_to or "HEAD",
        mode=mode,
        paths=args.paths or None,
        color=color,
    )
    if mode == "patch" and code == 0:
        if stdout_is_tty() and not args.no_color:
            # always show key (bright green can look odd on some themes)
            sys.stderr.write("  legend: \033[31m- deleted\033[0m   \033[1;92m+ added\033[0m\n")
        elif stdout_is_tty():
            sys.stderr.write("  legend: - deleted   + added\n")
        _page(text)
    else:
        sys.stdout.write(text)
        if text and not text.endswith("\n"):
            sys.stdout.write("\n")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
