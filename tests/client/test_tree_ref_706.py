"""#706: attach, move, prune and detach take a todo as ROSTER/NEED as well as its id, like label and watch."""
from __future__ import annotations

import pytest

from agent_coord.__main__ import _build_parser
from agent_coord.client.language import translate
from agent_coord.client.outbound import body_from_args
from agent_coord.helpers.errors import CoordError


@pytest.fixture(autouse=True)
def _clear_cli_office():
    from agent_coord.client.offices import bind_cli_office

    bind_cli_office("")
    yield
    bind_cli_office("")


def _body(argv):
    a = translate(_build_parser().parse_args(argv))
    return body_from_args(a)


def test_attach_by_name_sends_refs():
    body = _body(["attach", "agent-ux", "todo", "agent-ux/parent", "todo", "agent-ux/child"])
    assert body["ref_a"] == "agent-ux/parent" and body["ref_b"] == "agent-ux/child"
    assert "id_a" not in body and "id_b" not in body


def test_attach_mixes_name_and_number():
    body = _body(["attach", "agent-ux", "mail", "12", "todo", "agent-ux/child"])
    assert body["id_a"] == 12 and body["ref_b"] == "agent-ux/child" and "ref_a" not in body


def test_attach_by_number_unchanged():
    body = _body(["attach", "agent-ux", "todo", "3", "todo", "4"])
    assert body["id_a"] == 3 and body["id_b"] == 4 and "ref_a" not in body and "ref_b" not in body


def test_move_by_name_sends_refs():
    body = _body(["move", "agent-ux", "todo", "agent-ux/child", "todo", "agent-ux/parent"])
    assert body["ref"] == "agent-ux/child" and body["parent_ref"] == "agent-ux/parent"
    assert "id" not in body and "parent_id" not in body


@pytest.mark.parametrize("command", ["prune", "detach"])
def test_prune_detach_by_name(command):
    body = _body([command, "agent-ux", "todo", "agent-ux/child"])
    assert body["ref"] == "agent-ux/child" and "id" not in body


def test_bad_todo_word_refused_with_the_forms():
    with pytest.raises(CoordError) as ei:
        _body(["attach", "agent-ux", "todo", "child", "todo", "4"])
    assert str(ei.value).startswith("attach todo: give the todo id (a number above 0) or ROSTER/NEED")


def test_mail_by_word_refused_as_id():
    with pytest.raises(CoordError) as ei:
        _body(["attach", "agent-ux", "mail", "agent-ux/x", "todo", "4"])
    assert str(ei.value).startswith("attach mail: give the mail id")
