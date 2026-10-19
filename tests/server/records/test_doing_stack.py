"""join.doing stack: newest first, escaped separator, drop oldest at 512."""

from agent_coord.server.records.doing_stack import LIMIT, push, split


def test_push_puts_new_text_on_top() -> None:
    stored = push("present", "wake")
    assert stored == "wake | present"
    assert split(stored) == ["wake", "present"]


def test_pipe_and_backslash_are_escaped() -> None:
    stored = push("present", r"a | b\c")
    assert stored == r"a \| b\\c | present"
    assert split(stored) == [r"a | b\c", "present"]


def test_full_stack_drops_the_oldest_entry() -> None:
    stored = push("old", "x" * 400, limit=410)
    stored = push(stored, "y" * 400, limit=410)
    assert split(stored) == ["y" * 400]
    assert len(stored) <= 410


def test_one_entry_is_cut_to_the_column() -> None:
    stored = push("", "z" * 800, limit=LIMIT)
    assert len(stored) <= LIMIT
    assert split(stored) == ["z" * LIMIT]


def test_blank_text_leaves_the_stack() -> None:
    assert push("present", "  ") == "present"
