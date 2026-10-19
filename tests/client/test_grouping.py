"""List grouping: native default per list, --group-by override, refusals (#274)."""
import pytest

from agent_coord.__main__ import main
from agent_coord.client.grouping import apply, refusal

MAIL = [
    {"id": 1, "tree": "build-room", "sender": {"deskId": "a", "roster": "Office"}},
    {"id": 2, "sender": {"deskId": "b", "roster": "night"}},
    {"id": 3, "tree": "build-room", "sender": {"deskId": "c", "roster": "night"}},
]
TODOS = [
    {"id": 4, "project_id": "cold-test", "tree": "a1b2c3d4e5", "labels": ["urgent", "ux11"]},
    {"id": 7, "project_id": "cold-test", "tree": "a1b2c3d4e5", "labels": []},
    {"id": 9, "project_id": "the-mill", "tree": None, "labels": ["urgent"]},
    {"id": 2, "project_id": "the-mill", "tree": "ffff000011", "labels": None},
]
HOLDS = {
    "ok": True,
    "project": "Office",
    "holds": [
        {"resource": "build", "owner": "a", "roster": "the-mill", "labels": ["ci"]},
        {"resource": "deploy", "owner": "b", "roster": None, "labels": []},
    ],
}


def _keys(out):
    return [(g["key"], [r.get("id", r.get("resource")) for r in g["items"]]) for g in out["groups"]]


def test_inbox_defaults_to_room_tree():
    out, note = apply("inbox", MAIL)
    assert note == "" and out["group_by"] == "tree"
    assert _keys(out) == [("build-room", [1, 3]), ("(none)", [2])]


def test_inbox_group_by_roster():
    out, _ = apply("inbox", MAIL, "roster")
    assert [g["key"] for g in out["groups"]] == ["Office", "night"]


def test_todo_defaults_to_plan_tree_keeping_wall_order():
    out, note = apply("todo", TODOS)
    assert note == "" and out["group_by"] == "tree"
    assert _keys(out) == [("a1b2c3d4e5", [4, 7]), ("ffff000011", [2]), ("(none)", [9])]


def test_todo_default_with_no_plans_stays_flat():
    rows = [{"id": 1, "project_id": "cold-test", "tree": None}]
    assert apply("todo", rows) == (rows, "")


def test_todo_group_by_label_lists_a_card_under_each_label():
    out, _ = apply("todo", TODOS, "label")
    assert _keys(out) == [("urgent", [4, 9]), ("ux11", [4]), ("(none)", [7, 2])]


def test_todo_group_by_roster():
    out, _ = apply("todo", TODOS, "roster")
    assert _keys(out) == [("cold-test", [4, 7]), ("the-mill", [9, 2])]


def test_asked_group_with_no_values_is_one_none_group_no_note():
    out, note = apply("todo", [{"id": 1}], "label")
    assert note == "" and _keys(out) == [("(none)", [1])]


def test_holds_default_flat():
    assert apply("hold", HOLDS) == (HOLDS, "")


@pytest.mark.parametrize("by,want", [("label", [("ci", ["build"]), ("(none)", ["deploy"])]),
                                     ("roster", [("the-mill", ["build"]), ("(none)", ["deploy"])])])
def test_holds_group_by(by, want):
    out, note = apply("hold", HOLDS, by)
    assert note == "" and _keys(out) == want and out["project"] == "Office" and "holds" not in out


def test_empty_list_stays_empty():
    assert apply("todo", [], "label") == ([], "")


@pytest.mark.parametrize(
    "cmd,by,ok",
    [("todo", "tree", True), ("todo", "label", True), ("todo", "roster", True),
     ("inbox", "tree", True), ("inbox", "roster", True), ("inbox", "label", False),
     ("hold", "label", True), ("hold", "roster", True), ("hold", "tree", False),
     ("todo", "", True), ("send", "tree", True)],
)
def test_refusal_table(cmd, by, ok):
    assert (refusal(cmd, by) == "") is ok


def test_refusal_lines_name_the_choices():
    assert refusal("inbox", "label") == "inbox --group-by label: mail has no labels yet; use --group-by tree|roster"
    assert refusal("hold", "tree") == "hold --group-by tree: holds sit on no tree; use --group-by label|roster"


@pytest.mark.parametrize("argv", [["inbox", "--group-by", "label"], ["hold", "--group-by", "tree"]])
def test_never_applies_exits_2_one_line(argv, capsys):
    rc = main(argv)
    err = capsys.readouterr().err.strip().splitlines()
    assert rc == 2
    assert err[-1].startswith(f"{argv[0]} --group-by {argv[2]}: ")
