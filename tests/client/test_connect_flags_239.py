"""connect takes no unread flags (#239). Removed flags are an argparse refusal."""
from __future__ import annotations

import pytest

from agent_coord.__main__ import _build_parser


@pytest.mark.parametrize("flag", ["--doing", "--root", "--role", "--reset", "--verbose"])
def test_removed_connect_flags_refuse(flag) -> None:
    argv = ["connect", "the-mill", "d239", flag] + ([] if flag in ("--reset", "--verbose") else ["x"])
    with pytest.raises(SystemExit) as ei:
        _build_parser().parse_args(argv)
    assert ei.value.code == 2


def test_global_verbose_still_reaches_connect() -> None:
    args = _build_parser().parse_args(["--verbose", "connect", "the-mill", "d239"])
    assert args.verbose is True
