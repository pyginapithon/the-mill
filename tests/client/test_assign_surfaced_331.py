"""assign is the hand-off verb; help and the desk skill name it and its limits (#331)."""
from __future__ import annotations

import pathlib

from agent_coord.__main__ import _build_parser

ROOT = pathlib.Path(__file__).resolve().parents[2]


def _assign_help() -> str:
    parser = _build_parser()
    for action in parser._subparsers._group_actions:  # noqa: SLF001 - argparse has no public walk
        for choice in action._choices_actions:  # noqa: SLF001
            if choice.dest == "assign":
                return choice.help or ""
    raise AssertionError("no assign subcommand")


def test_help_names_unassigned_and_the_handoff():
    text = _assign_help()
    assert "unassigned" in text
    assert "unclaim" in text
    assert "Chief" not in text


def test_skill_names_the_handoff():
    skill = (ROOT / "docs" / "protocol" / "skill.md").read_text()
    assert "To hand a card to a named desk: `unclaim` it, then `assign <roster> <need> <desk>`" in skill


def test_cli_desk_assign_row_names_the_handoff():
    desk = (ROOT / "docs" / "protocol" / "cli-desk.md").read_text()
    row = next(line for line in desk.splitlines() if line.startswith("| `assign` |"))
    assert "unassigned" in row and "unclaim" in row
