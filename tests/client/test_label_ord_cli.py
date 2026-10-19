"""label --ord and trail --label on the CLI (no SQL, #198 #199)."""
from __future__ import annotations

import pytest

from agent_coord.helpers.label_ord import parse_label_ord
from agent_coord.helpers.errors import CoordError


def test_render_label_rows():
    from agent_coord.helpers.trail_text import render

    text = render(
        {
            "label": "bug",
            "hint": "",
            "rows": [
                {
                    "type": "todo",
                    "id": 3,
                    "ord": 0,
                    "need": "ship",
                    "body": "",
                    "created": "2026-01-01 00:00:00",
                }
            ],
            "truncated": False,
        }
    )
    assert text.splitlines()[0] == "trail --label bug: 1 row(s)"
    assert "todo 3 ord 0 ship 2026-01-01 00:00:00" in text
    assert text.isascii()
    hinted = render(
        {
            "label": "nope",
            "hint": "label: no name nope. mill label nope nope --yes",
            "rows": [],
            "truncated": False,
        }
    )
    assert "mill label nope nope --yes" in hinted


def test_parse_label_ord_range():
    assert parse_label_ord(None) is None
    assert parse_label_ord(0) == 0
    assert parse_label_ord("65535") == 65535
    for bad in (65536, -1, "nope", "1.5", True):
        with pytest.raises(CoordError, match="65535"):
            parse_label_ord(bad)


def test_label_add_help_lists_ord(capsys):
    from agent_coord.__main__ import main

    with pytest.raises(SystemExit) as ei:
        main(["label", "-h"])
    assert ei.value.code == 0
    assert "--ord" in capsys.readouterr().out


def test_trail_help_lists_label(capsys):
    from agent_coord.__main__ import main

    with pytest.raises(SystemExit) as ei:
        main(["trail", "-h"])
    assert ei.value.code == 0
    assert "--label" in capsys.readouterr().out


def test_label_add_cli_refuses_bad_ord(capsys):
    from agent_coord.__main__ import main

    for bad in ("65536", "-1", "nope"):
        with pytest.raises(SystemExit) as ei:
            main(["label", "todo", "1", "bug", "--ord", bad])
        assert ei.value.code not in (0, None)
        assert "65535" in capsys.readouterr().err
