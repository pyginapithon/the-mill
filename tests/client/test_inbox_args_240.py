"""inbox takes no project, desk, role, mark, or star argument (#240)."""
from __future__ import annotations

import pytest

from agent_coord.__main__ import _build_parser


@pytest.mark.parametrize(
    "argv",
    [
        ["inbox", "the-mill"],
        ["inbox", "the-mill", "desk"],
        ["inbox", "--role", "x"],
        ["inbox", "--mark"],
        ["inbox", "--no-mark"],
        ["inbox", "--star"],
        ["inbox", "--no-star"],
        ["inbox", "--after", "5"],
    ],
)
def test_removed_inbox_args_refuse(argv) -> None:
    with pytest.raises(SystemExit) as ei:
        _build_parser().parse_args(argv)
    assert ei.value.code == 2


def test_inbox_keeps_catch_up_flags() -> None:
    a = _build_parser().parse_args(["inbox", "--all", "--limit", "3"])
    assert (a.all, a.limit) == (True, 3)
    assert "after" not in vars(a)  # #254: mark is the cursor
