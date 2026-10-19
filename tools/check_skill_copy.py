"""Fail when a copy of the desk skill differs from docs/protocol/skill.md.

Usage:
  python tools/check_skill_copy.py                 # every in-repo copy
  python tools/check_skill_copy.py --installed     # also the installed pack's skill.md
  python tools/check_skill_copy.py PATH [PATH ...] # also these copies (a desk's SKILL.md)

A copy is any git-tracked Markdown file, other than the source, whose front
matter says `name: mill-desk`, plus every PATH given. Line endings are
normalized; every other byte must match. Exits 0 when every copy matches,
1 when any copy differs or is missing (with a unified diff and the copy
command that syncs it), 2 on bad usage.
"""
from __future__ import annotations

import argparse
import difflib
import shlex
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "protocol" / "skill.md"
NAME_LINE = "name: mill-desk"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def _front_name(text: str) -> bool:
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return False
    for line in lines[1:]:
        if line.strip() == "---":
            return False
        if line.strip() == NAME_LINE:
            return True
    return False


def repo_copies(root: Path = ROOT, source: Path = SOURCE) -> list[Path]:
    """Git-tracked Markdown files (not the source) that declare name: mill-desk."""
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "ls-files", "*.md"],
            capture_output=True, text=True, check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return []
    found = []
    for rel in out.splitlines():
        p = (root / rel).resolve()
        if p in (source.resolve(), SOURCE.resolve()) or not p.is_file():
            continue
        try:
            if _front_name(_text(p)):
                found.append(p)
        except (OSError, UnicodeDecodeError):
            continue
    return found


def installed_copy() -> Path | None:
    from agent_coord.install.host import installed_skill_md

    got = installed_skill_md()
    return Path(got) if got else None


def check(source: Path, copies: list[Path]) -> list[str]:
    """One report block per copy that differs; empty when all match."""
    want = _text(source)
    bad = []
    for c in copies:
        if not c.is_file():
            bad.append(f"MISSING {c}\n  sync: cp {shlex.quote(str(source))} {shlex.quote(str(c))}")
            continue
        got = _text(c)
        if got == want:
            continue
        diff = "".join(difflib.unified_diff(
            want.splitlines(keepends=True), got.splitlines(keepends=True),
            fromfile=str(source), tofile=str(c), n=1,
        ))
        bad.append(f"DRIFT {c}\n{diff}  sync: cp {shlex.quote(str(source))} {shlex.quote(str(c))}")
    return bad


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("copies", nargs="*", type=Path, help="extra copies to check (a desk SKILL.md)")
    ap.add_argument("--installed", action="store_true", help="also check the installed pack's skill.md")
    ap.add_argument("--source", type=Path, default=SOURCE, help="source of truth (default docs/protocol/skill.md)")
    a = ap.parse_args(argv)
    if not a.source.is_file():
        print(f"check_skill_copy: no source {a.source}", file=sys.stderr)
        return 2
    copies = repo_copies(source=a.source) + list(a.copies)
    if a.installed:
        got = installed_copy()
        if got is None:
            print("check_skill_copy: --installed: no installed pack skill.md found", file=sys.stderr)
            return 1
        if got.resolve() == a.source.resolve():
            print("check_skill_copy: --installed resolved to the source itself; run with the pack installed and PYTHONPATH unset", file=sys.stderr)
            return 1
        copies.append(got)
    bad = check(a.source, copies)
    for b in bad:
        print(b)
    print(f"check_skill_copy: {len(copies)} copies, {len(bad)} differ")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
