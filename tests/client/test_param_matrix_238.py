"""Every CLI verb and argument has a matrix row (#238).

The row list is tests/client/param_rows_238.txt. A new verb or flag
fails this file until that list gains the row. Omitting a required
positional exits 2 before any write.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from agent_coord.__main__ import _build_parser

_ROWS = Path(__file__).with_name("param_rows_238.txt")
_EXTRA = (
    "session heartbeat",
    "floor alive",
    "connect hint",
)

# Cards #231-#237. Behavior lives on those MRs. This list is the row
# each of them adds. session heartbeat, floor alive, and the connect
# hint are not parser flags; they stay as extra rows.
CARD_ROWS = (
    "create todo status",
    "claim eta",
    "claim msg",
    "pass need",
    "unclaim need",
    "unpark need",
    "hold peek",
    "send roster",
    "reply roster",
    "add kind",
    "add group",
    "add hint",
    "remove kind",
    "remove group",
    "connected project",
    "connect project",
    "hold resource",
    "session heartbeat",
    "floor alive",
    "connect hint",
)


def walk_rows(parser: argparse.ArgumentParser | None = None) -> list[str]:
    parser = parser or _build_parser()
    found: list[str] = []

    def walk(sub: argparse.ArgumentParser, prefix: str) -> None:
        for act in sub._actions:
            if isinstance(act, argparse._SubParsersAction):
                for name, child in act.choices.items():
                    path = (prefix + " " + name).strip()
                    found.append(path + " (verb)")
                    walk(child, path)
                continue
            if act.dest == "help":
                continue
            cmd = prefix.strip() or "(mill)"
            found.append(cmd + " " + act.dest)

    walk(parser, "")
    # Stable unique list. Duplicate dests on one command collapse.
    out: list[str] = []
    seen: set[str] = set()
    for row in found:
        if row not in seen:
            seen.add(row)
            out.append(row)
    return out


def required_omissions(parser: argparse.ArgumentParser | None = None) -> list[tuple[list[str], str]]:
    """(argv that omits this required positional, row key)."""
    parser = parser or _build_parser()
    cases: list[tuple[list[str], str]] = []

    def walk(sub: argparse.ArgumentParser, words: list[str]) -> None:
        positionals = []
        for act in sub._actions:
            if isinstance(act, argparse._SubParsersAction):
                continue
            if act.option_strings or act.dest == "help":
                continue
            nargs = getattr(act, "nargs", None)
            required = bool(getattr(act, "required", False)) or nargs not in ("?", "*", "...")
            if nargs == argparse.REMAINDER:
                required = False
            positionals.append((act.dest, required))
        filled: list[str] = []
        for dest, required in positionals:
            if not required:
                continue
            cmd = " ".join(words) if words else "(mill)"
            cases.append((words + filled, cmd + " " + dest))
            filled.append("x")
        for act in sub._actions:
            if isinstance(act, argparse._SubParsersAction):
                for name, child in act.choices.items():
                    walk(child, words + [name])

    walk(parser, [])
    return cases


def _saved_lines() -> list[str]:
    return [line for line in _ROWS.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_parser_rows_match_the_matrix() -> None:
    live = walk_rows()
    saved = [line for line in _saved_lines() if line not in _EXTRA]
    assert live == saved


def test_card_rows_are_in_the_matrix() -> None:
    saved = set(_saved_lines())
    missing = [row for row in CARD_ROWS if row not in saved]
    assert missing == []
    for extra in _EXTRA:
        assert extra in saved


def _case_id(item: object) -> str:
    if isinstance(item, list):
        return "omit " + (" ".join(item) or "(empty)")
    return str(item)


@pytest.mark.parametrize("argv,row", required_omissions(), ids=_case_id)
def test_omitting_a_required_positional_exits_2(argv, row) -> None:
    parser = _build_parser()
    with pytest.raises(SystemExit) as ei:
        parser.parse_args(argv)
    assert int(ei.value.code or 0) == 2


def test_every_book_argument_has_a_kind() -> None:
    from tests.client import param_cases_238 as pc

    assert pc.unclassified(_build_parser()) == []


def test_gaps_name_real_cases_and_cards() -> None:
    import re

    from tests.client import param_cases_238 as pc
    from tests.client.param_gaps_238 import GAPS

    ids = {pc.case_id(v, d, c) for v, d, c, _ in pc.build_cases(_build_parser())}
    assert sorted(set(GAPS) - ids) == []
    assert all(re.match(r"#2\d\d\b", why) for why in GAPS.values())


@pytest.mark.parametrize(
    "argv",
    [
        ["mail-thread", "1", "--all"],
        ["mail-thread", "1", "--no-mark"],
        ["mark", "1", "--state", "handled"],
        ["mark", "1", "--state", "later"],
    ],
)
def test_242_removed_flags_exit_2(argv: list[str]) -> None:
    """#242 rows: these calls error. Nothing is parsed through."""
    with pytest.raises(SystemExit) as ei:
        _build_parser().parse_args(argv)
    assert int(ei.value.code or 0) == 2


def test_242_kept_flags_still_parse() -> None:
    room = _build_parser().parse_args(["mail-thread", "9", "--room", "--after", "4"])
    assert room.scope == "room" and room.after == 4
    assert _build_parser().parse_args(["mail-thread", "9", "--subtree"]).scope == "subtree"
    assert _build_parser().parse_args(["mail-thread", "9", "--full"]).scope == "full"
    marked = _build_parser().parse_args(["mark", "3", "4"])
    assert marked.ids == ["3", "4"]
    assert "state" not in vars(marked)


@pytest.mark.parametrize(
    "argv",
    [
        ["file", "todo", "the-mill", "n"],
        ["ask"],
        ["hold", "the-mill", "docs/a.md", "--lease", "60"],
        ["trail", "1", "--type", "mail"],
        ["register", "the-mill"],
        ["agents", "the-mill"],
    ],
)
def test_247_alias_calls_exit_2(argv: list[str]) -> None:
    """#247: old names are not verbs or flags."""
    with pytest.raises(SystemExit) as ei:
        _build_parser().parse_args(argv)
    assert int(ei.value.code or 0) == 2
