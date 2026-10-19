"""#274 item 10: list rows carry the plan and labels; the wall sorts them stably.

Real book. mill_todo_select adds tree_id, tree and labels (JSON, label order),
sorted by plan then id. mill_hold_select adds labels, sorted by id. The label
lookup reads the label primary key, the plan lookup tree.idx_activity.
"""
from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from agent_coord.server.api.mill.rpc import _h_todo, _hold_list, _json_names
from agent_coord.server.records import hold as rec_hold
from agent_coord.server.records import label as rec_label
from agent_coord.server.records import todo as rec_todo
from agent_coord.server.records import tree as rec_tree
from agent_coord.server.records.db import call
from tests.server.records.conftest import seed_names

pytestmark = pytest.mark.sql

R = "gb274"


def _card(cn, need):
    return int(rec_todo.insert(cn, R, "gb_a", "open", json.dumps({"slug": need}))[0]["id"])


@pytest.fixture(scope="module")
def board(cn):
    seed_names(cn, (R, "roster"), ("gb_a", "desk"), ("gb-urgent", "label"), ("gb-ux", "label"), ("gb-ci", "label"))
    a, b, c, d = (_card(cn, n) for n in ("gb-a", "gb-b", "gb-c", "gb-d"))
    # Plan p2 is created first, so it has the lower plan id.
    rec_tree.create(cn, "gb274p2", "todo", d)
    rec_tree.create(cn, "gb274p1", "todo", b)
    rec_tree.add(cn, "todo", b, "todo", a, "gb274p1")
    rec_tree.add(cn, "todo", d, "todo", b, "gb274p2")  # b sits on two plans
    rec_label.put(cn, "todo", a, "gb-ux", 2)
    rec_label.put(cn, "todo", a, "gb-urgent", 1)
    rec_label.put(cn, "todo", c, "gb-urgent")
    rec_hold.upsert(cn, R, "gb_a", "gb274-res1")
    rec_hold.upsert(cn, R, "gb_a", "gb274-res2")
    hid = [h for h in rec_hold.select(cn, R) if h.get("resource") == "gb274-res1"][0]["id"]
    rec_label.put(cn, "hold", int(hid), "gb-ci")
    return {"a": a, "b": b, "c": c, "d": d}


def _plan_id(cn, name):
    return next(int(r["name_id"]) for r in rec_tree.select(cn, name))


def test_todo_rows_carry_plan_and_labels_sorted_by_plan_then_id(cn, board):
    rows = [r for r in call(cn, "mill_todo_select", [R, ""]) if r.get("roster") == R]
    p1, p2 = _plan_id(cn, "gb274p1"), _plan_id(cn, "gb274p2")
    assert p2 < p1
    got = [(int(r["id"]), r["tree_id"], r["tree"], _json_names(r["labels"])) for r in rows]
    a, b, c, d = board["a"], board["b"], board["c"], board["d"]
    assert got == [
        (b, p2, "gb274p2", []),  # two plans: listed under the lower plan id
        (d, p2, "gb274p2", []),
        (a, p1, "gb274p1", ["gb-urgent", "gb-ux"]),  # label order (ord), not insert order
        (c, None, None, ["gb-urgent"]),  # no plan: last
    ]


def test_todo_handler_rows_name_tree_and_labels(cn, board):
    out = _h_todo(SimpleNamespace(_cn=cn), {"verb": "todo"}, R, "gb_a")
    rows = out if isinstance(out, list) else out.get("result") or out
    by_id = {int(r["id"]): r for r in rows}
    assert by_id[board["a"]]["tree"] == "gb274p1" and by_id[board["a"]]["labels"] == ["gb-urgent", "gb-ux"]
    assert by_id[board["c"]]["tree"] is None and by_id[board["c"]]["labels"] == ["gb-urgent"]


def test_hold_rows_carry_labels_and_roster_sorted_by_id(cn, board):
    out = _hold_list(SimpleNamespace(_cn=cn), R)
    mine = [h for h in out["holds"] if str(h["resource"]).startswith("gb274-")]
    assert [h["resource"] for h in mine] == ["gb274-res1", "gb274-res2"]
    assert mine[0]["labels"] == ["gb-ci"] and mine[1]["labels"] == []
    assert mine[0]["roster"]  # the roster the hold activity row carries
    ids = [int(h["id"]) for h in out["holds"]]
    assert ids == sorted(ids)


def test_label_and_plan_lookups_use_an_index(cn, board):
    cur = cn.cursor(dictionary=True)
    try:
        cur.execute(
            "EXPLAIN SELECT l.name_id FROM label l WHERE l.type = 'todo' AND l.id = %s", (board["a"],)
        )
        lab = cur.fetchall()
        cur.execute(
            "EXPLAIN SELECT x.name_id FROM tree x WHERE x.type = 'todo' AND x.id = %s", (board["a"],)
        )
        plan = cur.fetchall()
    finally:
        cur.close()
    assert lab[0]["key"] == "PRIMARY", lab
    assert plan[0]["key"] in ("idx_activity", "PRIMARY"), plan


@pytest.mark.parametrize("raw,want", [(None, []), ("", []), ('["a","b"]', ["a", "b"]), ("not json", []),
                                      ('{"a":1}', []), (b'["x"]', ["x"]), ('["a",1]', ["a"])])
def test_json_names(raw, want):
    assert _json_names(raw) == want
