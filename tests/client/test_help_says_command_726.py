"""F108 (help-says-command): every mill help page says command, not verb (#726)."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import agent_coord.__main__ as cli

WORD = re.compile(r"(?i)\bverbs?\b")
ROOT = Path(__file__).resolve().parents[2]


def _pages() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []

    def walk(p: argparse.ArgumentParser, path: str) -> None:
        out.append((path, p.format_help()))
        for a in p._actions:
            if isinstance(a, argparse._SubParsersAction):
                for name, sub in a.choices.items():
                    walk(sub, f"{path} {name}")

    walk(cli._build_parser(), "mill")
    return out


def test_no_help_page_says_verb() -> None:
    pages = _pages()
    assert len(pages) > 40
    bad = [f"{path}: {line.strip()}" for path, text in pages for line in text.splitlines() if WORD.search(line)]
    assert bad == []


def test_top_usage_names_command() -> None:
    usage = cli._build_parser().format_usage()
    assert "COMMAND ..." in usage and "VERB" not in usage


def test_help_positional_is_command() -> None:
    pages = dict(_pages())
    assert "[command]" in pages["mill help"]


def test_wall_score_pane_text_says_command() -> None:
    html = (ROOT / "agent_coord" / "web" / "wall_ui" / "default" / "board.html").read_text(encoding="utf-8")
    text = re.sub(r"<[^>]*>", " ", html)
    assert not WORD.search(text)
    assert 'aria-label="Commands"' in html
