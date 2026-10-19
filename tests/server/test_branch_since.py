"""Branch slice for the mail-thread read cursor (#155, #190). No database."""
from __future__ import annotations

from agent_coord.server.api.mill.rpc import _branch_since


def test_first_read_is_the_whole_branch():
    assert _branch_since([1, 2, 3], 3, 0) == [1, 2, 3]


def test_later_read_skips_letters_already_served():
    assert _branch_since([1, 2, 3, 4], 4, 2) == [3, 4]


def test_reread_is_the_letter_alone():
    assert _branch_since([1, 2, 3], 3, 3) == [3]
