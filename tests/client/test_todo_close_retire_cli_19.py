"""mill retire todo / mill reclaim todo / pass with a comma list (#19). Row F103."""
from __future__ import annotations

from agent_coord.__main__ import _build_parser
from agent_coord.client.language import translate
from agent_coord.client.outbound import body_from_args


def _body(argv):
    args = _build_parser().parse_args(argv)
    args = translate(args, ask=lambda _q: "y")
    return body_from_args(args)


def test_retire_todo_sends_the_roster_and_the_need():
    body = _body(["retire", "todo", "unit", "n1,n2", "--yes"])
    assert body["verb"] == "retire"
    assert body["name_type"] == "todo"
    assert body["project"] == "unit"
    assert body["need"] == "n1,n2"


def test_reclaim_todo_sends_the_roster_and_the_need():
    body = _body(["reclaim", "todo", "unit", "n1", "--yes"])
    assert body["verb"] == "reclaim"
    assert body["name_type"] == "todo"
    assert body["project"] == "unit"
    assert body["need"] == "n1"


def test_pass_done_sends_a_comma_list_whole():
    body = _body(["pass", "unit", "a,b,c", "--done"])
    assert body["need"] == "a,b,c" and body["step"] == "done"
