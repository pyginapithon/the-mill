"""mill pass --done / --back send the step; plain pass sends ship (#615). Row F67 (pass-step)."""
from __future__ import annotations

import pytest

from agent_coord.__main__ import _build_parser
from agent_coord.client.outbound import body_from_args


@pytest.mark.parametrize("argv,step", [
    (["pass", "unit", "n1"], "ship"),
    (["pass", "unit", "n1", "--done"], "done"),
    (["pass", "unit", "n1", "--back"], "back"),
])
def test_the_cli_sends_the_step(argv, step):
    args = _build_parser().parse_args(argv)
    body = body_from_args(args)
    assert body["step"] == step


def test_done_and_back_together_are_refused():
    with pytest.raises(SystemExit):
        _build_parser().parse_args(["pass", "unit", "n1", "--done", "--back"])
