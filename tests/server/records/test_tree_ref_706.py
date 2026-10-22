"""#706: the tree verbs resolve a todo named ROSTER/NEED to its id on the wall (as #274)."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from agent_coord.helpers.errors import CoordError
from agent_coord.server.api.mill.rpc import _h_attach, _h_detach, _tree_id
from agent_coord.server.records import todo as rec_todo
from agent_coord.server.records.db import scalar
from tests.server.records.conftest import seed_names

pytestmark = pytest.mark.sql

R = "tr706"


def _c(cn):
    return SimpleNamespace(_cn=cn)


@pytest.fixture(scope="module")
def board(cn):
    seed_names(cn, (R, "roster"), ("tr_a", "desk"))
    ids = {}
    for need in ("parent", "child"):
        ids[need] = int(rec_todo.insert(cn, R, "tr_a", "open", '{"slug": "%s", "doing": "x"}' % need)[0]["id"])
    return ids


def test_tree_id_resolves_ref(cn, board):
    assert _tree_id(_c(cn), "todo", None, f"{R}/child", "attach") == board["child"]
    assert _tree_id(_c(cn), "todo", board["parent"], None, "attach") == board["parent"]


def test_tree_id_unknown_card_names_the_verb(cn, board):
    with pytest.raises(CoordError) as ei:
        _tree_id(_c(cn), "todo", None, f"{R}/nope", "attach")
    assert str(ei.value).startswith(f"attach: no card nope in {R}")


def test_attach_and_detach_by_name(cn, board):
    before = scalar(cn, "SELECT COUNT(*) FROM tree")
    body = {"type_a": "todo", "ref_a": f"{R}/parent", "type_b": "todo", "ref_b": f"{R}/child"}
    _h_attach(_c(cn), body, R, "tr_a")
    assert scalar(cn, "SELECT COUNT(*) FROM tree") > before
    _h_detach(_c(cn), {"type": "todo", "ref": f"{R}/child"}, R, "tr_a")
