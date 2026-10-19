"""mill trail: CLI body, text render, PT clock (no SQL)."""
from __future__ import annotations

import json
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

from agent_coord.helpers.ptime import pt_label, utc_to_pt
from agent_coord.helpers.trail_text import mark_of, node_line, render


def test_pt_label_dst_and_standard():
    assert pt_label(datetime(2026, 10, 9, 11, 30)) == "2026-10-09 04:30 PT"
    assert pt_label(datetime(2026, 12, 1, 20, 0)) == "2026-12-01 12:00 PT"
    assert pt_label(None) == ""


def test_pt_fallback_matches_zoneinfo():
    for dt in (
        datetime(2026, 3, 8, 9, 59),
        datetime(2026, 3, 8, 10, 0),
        datetime(2026, 11, 1, 8, 59),
        datetime(2026, 11, 1, 9, 0),
        datetime(2026, 7, 4, 0, 0),
    ):
        assert utc_to_pt(dt, use_zoneinfo=False) == utc_to_pt(dt)


def test_marks():
    assert mark_of("dead-end: rerun gives same error") == "DEAD END"
    assert mark_of("Dead-End: x") == "DEAD END"
    assert mark_of("solved: git abc123") == "SOLVED"
    assert mark_of("solved (unexpected): git abc123") == "SOLVED"
    assert mark_of("SOLVED (unexpected): git abc123") == "SOLVED"
    assert mark_of("dead end (nope): stop") == "DEAD END"
    assert mark_of("tried again") == ""
    assert mark_of("unsolved: still open") == ""


def test_node_line_truncates_and_indents():
    line = node_line({"kind": "todo", "id": 7, "depth": 2, "state": "done", "mark": "DEAD END",
                      "title": "x" * 300, "last_note": "dead-end: y", "who": "tester", "at_pt": "2026-10-09 04:30 PT"})
    assert line.startswith("    todo 7 [done] [DEAD END] ")
    assert "..." in line
    assert line.endswith("(tester, 2026-10-09 04:30 PT)")


def test_render_header_counts():
    res = {"root": {"kind": "mail", "id": 1}, "tree": "agent-ux", "truncated": False,
           "nodes": [{"kind": "mail", "id": 1, "depth": 0, "state": "sent", "title": "finding"},
                     {"kind": "todo", "id": 2, "depth": 1, "state": "done", "mark": "DEAD END"},
                     {"kind": "todo", "id": 3, "depth": 1, "state": "shipped", "mark": "SOLVED"}]}
    text = render(res)
    assert text.splitlines()[0] == "trail mail 1 on agent-ux: 3 node(s), 1 dead end(s), 1 solved"
    assert text.isascii()


def test_trail_is_a_verb_and_body_carries_node():
    from agent_coord.client.outbound import VERBS, WALL, body_from_args

    assert "trail" in VERBS and "trail" in WALL
    args = SimpleNamespace(cmd="trail", node="mail:1188", type="", as_json=False)
    with patch("agent_coord.client.tokens.resolve_desk_owner", return_value="me"):
        body = body_from_args(args)
    assert body["verb"] == "trail" and body["node"] == "mail:1188"


def test_parser_accepts_trail():
    from agent_coord import __main__ as m

    seen = {}

    def fake(args):
        seen["args"] = args
        return 0

    with patch("agent_coord.client.http.mill_http_from_args", side_effect=fake), patch(
        "agent_coord.client.http.mill_url", return_value="https://wall"
    ):
        rc = m.main(["trail", "todo:63", "--json"])
    assert rc == 0
    assert seen["args"].node == "todo:63" and seen["args"].as_json is True


def test_http_prints_text_unless_json(capsys):
    from agent_coord.client import http

    reply = {"ok": True, "result": {"root": {"kind": "todo", "id": 5}, "tree": "", "nodes": [
        {"kind": "todo", "id": 5, "depth": 0, "state": "open", "title": "t"}]}}
    with patch.object(http, "mill_http_call", return_value=reply), patch(
        "agent_coord.client.outbound.body_from_args", return_value={"verb": "trail"}
    ):
        rc = http.mill_http_from_args(SimpleNamespace(cmd="trail", as_json=False))
        out = capsys.readouterr().out
        assert rc == 0 and out.startswith("trail todo 5 (not on a tree)")
        rc = http.mill_http_from_args(SimpleNamespace(cmd="trail", as_json=True))
        out = capsys.readouterr().out
        assert rc == 0 and json.loads(out)["result"]["root"]["id"] == 5


def test_render_header_tree_states():
    from agent_coord.helpers.trail_text import render

    one = [{"kind": "mail", "id": 7, "depth": 0, "state": "sent", "title": "t"}]
    two = one + [{"kind": "mail", "id": 8, "depth": 1, "state": "sent", "title": "u"}]
    base = {"root": {"kind": "mail", "id": 7}}
    assert "(not on a tree)" in render({**base, "tree": "", "on_tree": False, "nodes": one})
    assert " on an unnamed tree" in render({**base, "tree": "", "on_tree": True, "nodes": one})
    assert " on an unnamed tree" in render({**base, "tree": "", "nodes": two})
    assert " on agent-ux:" in render({**base, "tree": "agent-ux", "on_tree": True, "nodes": two})
