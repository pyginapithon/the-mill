"""F22: plain `mill todo` / `--all` is one todo call; an older wall answer is a clear error (alpha)."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

import agent_coord.client.http as http
import agent_coord.server.api.mill.rpc as rpc
from agent_coord.helpers.errors import CoordError

ROSTERS = ["Office", "cold-test", "the-mill"]
CARDS = {r: [{"project_id": r, "need_id": f"n-{r}"}] for r in ROSTERS}


def _wall(new: bool, calls: list):
    def fake(b):
        calls.append((b["verb"], b.get("project"), tuple(b.get("rosters") or ())))
        if b["verb"] == "project":
            return {"ok": True, "result": {"projects": list(ROSTERS)}}
        if b["verb"] == "member":
            return {"ok": True, "result": [{"slot": "Office"}, {"slot": "cold-test"}]}
        if new and "rosters" in b:
            cards = [c for r in b["rosters"] for c in CARDS.get(r, [])]
            return {"ok": True, "result": {"cards": cards, "rosters": len(b["rosters"])}}
        return {"ok": True, "result": list(CARDS.get(b["project"], []))}

    return fake


def _run(monkeypatch, new: bool, all_: bool):
    calls: list = []
    monkeypatch.setattr(http, "mill_http_call", _wall(new, calls))
    a = SimpleNamespace(cmd="todo", project="", need="", all=all_)
    return http._todo_call(a, {"verb": "todo", "project": "the-mill", "owner": "me"}), calls


def test_all_is_one_todo_call(monkeypatch):
    got, calls = _run(monkeypatch, True, True)
    assert [c[0] for c in calls].count("todo") == 1
    assert got["note"] == "every roster (3)"
    assert [r["project_id"] for r in got["result"]] == ROSTERS


def test_plain_is_one_todo_call(monkeypatch):
    got, calls = _run(monkeypatch, True, False)
    assert [c for c in calls if c[0] == "todo"] == [("todo", "Office", ("Office", "cold-test"))]
    assert [r["project_id"] for r in got["result"]] == ["Office", "cold-test"]


def test_older_wall_list_answer_is_an_error_not_a_loop(monkeypatch):
    with pytest.raises(CoordError, match="update the wall"):
        _run(monkeypatch, False, True)


def test_refused_read_is_returned_without_a_per_roster_loop(monkeypatch):
    calls: list = []
    base = _wall(True, calls)

    def fake(b):
        if b["verb"] == "todo" and "rosters" in b:
            calls.append(("todo", b.get("project"), tuple(b["rosters"])))
            return {"ok": False, "error": "todo: refused"}
        return base(b)

    monkeypatch.setattr(http, "mill_http_call", fake)
    a = SimpleNamespace(cmd="todo", project="", need="", all=True)
    got = http._todo_call(a, {"verb": "todo", "project": "the-mill", "owner": "me"})
    assert got == {"ok": False, "error": "todo: refused"}
    assert [c[0] for c in calls].count("todo") == 1


def test_many_rosters_read_in_chunks_of_the_wall_limit(monkeypatch):
    names = ["r%03d" % i for i in range(http.TODO_ROSTERS_PER_READ * 2 + 1)]
    sizes: list = []

    def fake(b):
        if b["verb"] == "project":
            return {"ok": True, "result": {"projects": list(names)}}
        sizes.append(len(b["rosters"]))
        assert len(b["rosters"]) <= rpc.TODO_ROSTERS_MAX
        return {"ok": True, "result": {"cards": [{"project_id": r} for r in b["rosters"]], "rosters": len(b["rosters"])}}

    monkeypatch.setattr(http, "mill_http_call", fake)
    a = SimpleNamespace(cmd="todo", project="", need="", all=True)
    got = http._todo_call(a, {"verb": "todo", "project": "the-mill", "owner": "me"})
    assert sizes == [200, 200, 1]
    assert [r["project_id"] for r in got["result"]] == names
    assert got["note"] == "every roster (%d)" % len(names)


def test_client_chunk_matches_wall_limit():
    assert http.TODO_ROSTERS_PER_READ == rpc.TODO_ROSTERS_MAX
