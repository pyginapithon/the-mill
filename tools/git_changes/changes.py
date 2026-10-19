"""Human-facing: pretty diff between two git versions (cross-platform)."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class RevPair:
    old: str
    new: str
    old_label: str
    new_label: str
    how: str  # how old was chosen


def _git(args: Sequence[str], *, cwd: str | None = None) -> tuple[int, str, str]:
    git = shutil.which("git")
    if not git:
        return 127, "", "git not found on PATH"
    try:
        p = subprocess.run(
            [git, *args],
            cwd=cwd or None,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()
    except OSError as e:
        return 1, "", str(e)


def _color(enabled: bool) -> dict[str, str]:
    if not enabled:
        return {
            k: ""
            for k in (
                "reset",
                "bold",
                "dim",
                "green",
                "red",
                "cyan",
                "yellow",
                "magenta",
                "inv",
                "bright_green",
            )
        }
    return {
        "reset": "\033[0m",
        "bold": "\033[1m",
        "dim": "\033[2m",
        "green": "\033[32m",
        "bright_green": "\033[1;92m",
        "red": "\033[31m",
        "cyan": "\033[36m",
        "yellow": "\033[33m",
        "magenta": "\033[35m",
        "inv": "\033[7m",
    }


def _enable_windows_ansi() -> None:
    if os.name != "nt":
        return
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        mode = ctypes.c_uint32()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
    except Exception:
        pass


def _is_ancestor(maybe_old: str, tip: str, *, cwd: str | None = None) -> bool:
    code, _, _ = _git(["merge-base", "--is-ancestor", maybe_old, tip], cwd=cwd)
    return code == 0


def resolve_last_version(tip: str = "HEAD", *, cwd: str | None = None) -> tuple[str, str]:
    """Pick a sensible 'last version' relative to tip."""
    code, out, _ = _git(["describe", "--tags", "--abbrev=0", tip], cwd=cwd)
    if code == 0 and out and _is_ancestor(out, tip, cwd=cwd):
        return out, f"tag {out} (describe)"

    code, out, _ = _git(["tag", "-l", "v*", "--sort=-v:refname"], cwd=cwd)
    if code == 0 and out:
        for tag in out.splitlines():
            tag = tag.strip()
            if tag and _is_ancestor(tag, tip, cwd=cwd):
                return tag, f"tag {tag} (ancestor)"

    code, out, _ = _git(
        ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"], cwd=cwd
    )
    if code == 0 and out:
        return out, f"upstream {out}"

    for remote in ("origin/main", "origin/master"):
        code, _, _ = _git(["rev-parse", "--verify", remote], cwd=cwd)
        if code == 0:
            return remote, remote

    raise RuntimeError(
        "no last version found (no ancestor tag, no upstream, no origin/main). "
        "Pass --from explicitly."
    )


def resolve_pair(
    old: str | None,
    new: str | None,
    *,
    cwd: str | None = None,
) -> RevPair:
    new_rev = (new or "HEAD").strip() or "HEAD"
    how = "explicit"
    if old and old.strip():
        old_rev = old.strip()
        how = "explicit --from"
    else:
        old_rev, how = resolve_last_version(new_rev, cwd=cwd)
    _, new_short, _ = _git(["rev-parse", "--short", new_rev], cwd=cwd)
    _, old_short, _ = _git(["rev-parse", "--short", old_rev], cwd=cwd)
    return RevPair(
        old=old_rev,
        new=new_rev,
        old_label=old_rev if not old_short else f"{old_rev} ({old_short})",
        new_label=new_rev if new_rev != "HEAD" else f"HEAD ({new_short or '?'})",
        how=how,
    )


def list_names(pair: RevPair, *, cwd: str | None = None) -> list[str]:
    code, out, err = _git(["diff", "--name-only", f"{pair.old}...{pair.new}"], cwd=cwd)
    if code != 0:
        code2, out2, err2 = _git(["diff", "--name-only", f"{pair.old}..{pair.new}"], cwd=cwd)
        if code2 != 0:
            raise RuntimeError(err or err2 or "git diff failed")
        return [ln for ln in out2.splitlines() if ln.strip()]
    return [ln for ln in out.splitlines() if ln.strip()]


def name_status(pair: RevPair, *, cwd: str | None = None) -> list[tuple[str, str]]:
    code, out, err = _git(["diff", "--name-status", f"{pair.old}...{pair.new}"], cwd=cwd)
    if code != 0:
        code, out, err = _git(["diff", "--name-status", f"{pair.old}..{pair.new}"], cwd=cwd)
        if code != 0:
            raise RuntimeError(err or "git diff --name-status failed")
    rows: list[tuple[str, str]] = []
    for ln in out.splitlines():
        if not ln.strip():
            continue
        parts = ln.split("\t", 1)
        if len(parts) == 2:
            rows.append((parts[0].strip(), parts[1].strip()))
        else:
            rows.append(("?", ln.strip()))
    return rows


def shortstat(pair: RevPair, *, cwd: str | None = None) -> str:
    code, out, _ = _git(["diff", "--shortstat", f"{pair.old}...{pair.new}"], cwd=cwd)
    if code != 0:
        code, out, _ = _git(["diff", "--shortstat", f"{pair.old}..{pair.new}"], cwd=cwd)
    return out


def patch(pair: RevPair, paths: Sequence[str] | None = None, *, cwd: str | None = None) -> str:
    args = ["diff", f"{pair.old}...{pair.new}"]
    if paths:
        args += ["--", *paths]
    code, out, err = _git(args, cwd=cwd)
    if code != 0:
        args[1] = f"{pair.old}..{pair.new}"
        code, out, err = _git(args, cwd=cwd)
        if code != 0:
            raise RuntimeError(err or "git diff patch failed")
    return out


def _count_pm(lines: list[str]) -> tuple[int, int]:
    """Count added (+) and deleted (-) lines in a unified-diff file section."""
    plus = minus = 0
    for ln in lines:
        if ln.startswith("+") and not ln.startswith("+++"):
            plus += 1
        elif ln.startswith("-") and not ln.startswith("---"):
            minus += 1
    return plus, minus


def _file_header_bar(path: str, plus: int, minus: int, *, color: bool) -> str:
    c = _color(color)
    width = max(40, shutil.get_terminal_size((80, 24)).columns)
    # counts on the right of the bar
    counts = f"  +{plus}  -{minus}  "
    left = f" FILE  {path} "
    pad = width - len(left) - len(counts)
    if pad < 1:
        # path too long: trim path, keep counts
        keep = max(8, width - len(counts) - len(" FILE  ") - 1)
        left = f" FILE  {path[:keep]} "
        pad = max(1, width - len(left) - len(counts))
    label = left + (" " * pad) + counts
    if len(label) > width:
        label = label[:width]
    if not color:
        return label
    return f"{c['inv']}{c['bold']}{label}{c['reset']}"


def _colorize_line(ln: str, *, color: bool) -> str:
    c = _color(color)
    if not color:
        return ln
    if ln.startswith("+++ ") or ln.startswith("--- "):
        return f"{c['bold']}{c['cyan']}{ln}{c['reset']}"
    if ln.startswith("@@"):
        return f"{c['magenta']}{ln}{c['reset']}"
    if ln.startswith("+") and not ln.startswith("+++"):
        return f"{c['bright_green']}{ln}{c['reset']}"
    if ln.startswith("-") and not ln.startswith("---"):
        return f"{c['red']}{ln}{c['reset']}"
    if ln.startswith("index ") or ln.startswith("new file") or ln.startswith("deleted file"):
        return f"{c['dim']}{ln}{c['reset']}"
    if ln.startswith("diff --git"):
        return f"{c['dim']}{ln}{c['reset']}"
    return ln


def colorize_diff(text: str, *, color: bool) -> str:
    """Per-file header bar (+N -M), diff --git under it, colored +/- lines."""
    if not text:
        return text
    lines = text.splitlines()
    # split into sections starting at diff --git
    sections: list[list[str]] = []
    cur: list[str] = []
    for ln in lines:
        if ln.startswith("diff --git") and cur:
            sections.append(cur)
            cur = [ln]
        else:
            cur.append(ln)
    if cur:
        sections.append(cur)

    out: list[str] = []
    for sec in sections:
        if not sec:
            continue
        head = sec[0]
        body = sec[1:] if head.startswith("diff --git") else sec
        if head.startswith("diff --git"):
            m = re.match(r"diff --git a/(.+) b/(.+)$", head)
            path = m.group(2) if m else head
            plus, minus = _count_pm(sec)
            out.append("")
            out.append(_file_header_bar(path, plus, minus, color=color))
            out.append(_colorize_line(head, color=color))
            for ln in body:
                out.append(_colorize_line(ln, color=color))
        else:
            for ln in sec:
                out.append(_colorize_line(ln, color=color))
    return "\n".join(out) + ("\n" if text.endswith("\n") else "")


def format_pretty(pair: RevPair, rows: list[tuple[str, str]], stat: str, *, color: bool) -> str:
    c = _color(color)
    lines = [
        f"{c['bold']}git-changes{c['reset']}  {c['dim']}{pair.how}{c['reset']}",
        f"  {c['cyan']}{pair.old_label}{c['reset']}  ->  {c['cyan']}{pair.new_label}{c['reset']}",
    ]
    if stat:
        lines.append(f"  {c['dim']}{stat}{c['reset']}")
    lines.append("")
    if not rows:
        lines.append(f"  {c['dim']}(no file differences){c['reset']}")
        return "\n".join(lines)

    status_color = {
        "A": c["green"],
        "M": c["yellow"],
        "D": c["red"],
        "R": c["cyan"],
        "C": c["cyan"],
    }
    for st, path in rows:
        key = st[:1]
        sc = status_color.get(key, c["dim"])
        lines.append(f"  {sc}{st:<4}{c['reset']} {c['bold']}{path}{c['reset']}")
    lines.append("")
    lines.append(
        f"{c['dim']}tip: git-changes -v   (line diff, key to page)   --from TAG --to HEAD{c['reset']}"
    )
    return "\n".join(lines)


def run_changes(
    *,
    old: str | None = None,
    new: str | None = None,
    mode: str = "pretty",
    paths: Sequence[str] | None = None,
    cwd: str | None = None,
    color: bool | None = None,
) -> tuple[int, str]:
    """Returns (exit_code, text)."""
    try:
        code, _, err = _git(["rev-parse", "--is-inside-work-tree"], cwd=cwd)
        if code != 0:
            return 1, err or "not a git checkout"
        pair = resolve_pair(old, new, cwd=cwd)
        use_color = sys.stdout.isatty() if color is None else color
        if mode == "names":
            names = list_names(pair, cwd=cwd)
            if paths:
                want = set(paths)
                names = [n for n in names if n in want]
            return 0, "\n".join(names) + ("\n" if names else "")
        if mode == "stat":
            return 0, shortstat(pair, cwd=cwd) + "\n"
        if mode == "patch":
            raw = patch(pair, paths, cwd=cwd)
            return 0, colorize_diff(raw, color=use_color)
        rows = name_status(pair, cwd=cwd)
        if paths:
            want = set(paths)
            rows = [(s, p) for s, p in rows if p in want]
        stat = shortstat(pair, cwd=cwd)
        return 0, format_pretty(pair, rows, stat, color=use_color) + "\n"
    except RuntimeError as e:
        return 1, str(e) + "\n"


def stdout_is_tty() -> bool:
    try:
        return sys.stdout.isatty()
    except Exception:
        return False


def stderr_is_tty() -> bool:
    try:
        return sys.stderr.isatty()
    except Exception:
        return False


def _wait_key() -> str:
    """Block until a key. Space=page, n=next file, q/Ctrl+C=quit."""
    try:
        if os.name == "nt":
            import msvcrt

            ch = msvcrt.getwch()
            if ch in ("\x00", "\xe0"):
                msvcrt.getwch()
                return " "  # arrows -> next page
            if ch in ("\x03", "\x1b"):
                return "q"
            return ch
        import termios
        import tty

        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        if ch in ("\x03", "\x1b"):
            return "q"
        return ch
    except KeyboardInterrupt:
        return "q"
    except Exception:
        try:
            return input() or " "
        except (EOFError, KeyboardInterrupt):
            return "q"


def _file_starts(lines: list[str]) -> list[int]:
    starts: list[int] = []
    for idx, ln in enumerate(lines):
        if " FILE  " in ln:
            starts.append(idx)
    return starts


def _file_sections(lines: list[str]) -> list[tuple[int, int]]:
    starts = _file_starts(lines)
    if not starts:
        return [(0, len(lines))] if lines else []
    ranges: list[tuple[int, int]] = []
    if starts[0] > 0:
        ranges.append((0, starts[0]))
    for i, s in enumerate(starts):
        e = starts[i + 1] if i + 1 < len(starts) else len(lines)
        ranges.append((s, e))
    return ranges


def _clear_screen() -> None:
    _enable_windows_ansi()
    sys.stdout.write("\033[H\033[J")
    sys.stdout.flush()


def _page(text: str) -> None:
    """Classic more on TTY: page with Space, n = next file (starts at top).

    No sticky chrome - Windows Terminal scrollback can't float a header.
    Piped/redirect: raw stdout.
    """
    if not text:
        return
    body = text if text.endswith("\n") else text + "\n"
    if not stdout_is_tty():
        sys.stdout.write(body)
        return

    lines = body.splitlines(keepends=True)
    sections = _file_sections(lines)
    if not sections:
        sys.stdout.write(body)
        return

    c = _color(True)
    try:
        for si, (start, end) in enumerate(sections):
            sec = lines[start:end]
            _clear_screen()
            rows = max(4, shutil.get_terminal_size((80, 24)).lines)
            page_h = max(1, rows - 1)  # leave room for --More-- prompt
            i = 0
            while i < len(sec):
                chunk = sec[i : i + page_h]
                sys.stdout.write("".join(chunk))
                sys.stdout.flush()
                i += len(chunk)
                if i >= len(sec):
                    # end of this file - brief pause then next, or wait once
                    if si + 1 >= len(sections):
                        break
                    prompt = (
                        f"\n{c['inv']}{c['bold']}"
                        f" --End file {si + 1}/{len(sections)}-- "
                        f"n/Space next | q quit "
                        f"{c['reset']}"
                    )
                    sys.stdout.write(prompt)
                    sys.stdout.flush()
                    key = _wait_key()
                    sys.stdout.write("\r\033[K")
                    if key in ("q", "Q", "\x03"):
                        sys.stdout.write(f"{c['reset']}(stopped)\n")
                        return
                    break  # next file
                prompt = (
                    f"{c['inv']}{c['bold']}"
                    f" --More-- file {si + 1}/{len(sections)} "
                    f"Space page | n next file | q quit "
                    f"{c['reset']}"
                )
                sys.stdout.write(prompt)
                sys.stdout.flush()
                key = _wait_key()
                # erase prompt line
                sys.stdout.write("\r\033[K")
                sys.stdout.flush()
                if key in ("q", "Q", "\x03"):
                    sys.stdout.write(f"{c['reset']}(stopped)\n")
                    return
                if key in ("n", "N", "f", "F"):
                    break  # next file (clear happens at loop top)
                # Space / Enter / anything else -> next page
        sys.stdout.write(f"{c['reset']}(end)\n")
    except KeyboardInterrupt:
        sys.stdout.write(f"\n{c['reset']}(stopped)\n")
