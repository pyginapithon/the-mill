"""Floor roster reads: blanks dropped, one IN helper read, never one read per name."""
from __future__ import annotations

from agent_coord.server.records import floor


def _boom(*_a, **_k):
    raise AssertionError("per-name read must not run")


def _wire(monkeypatch):
    calls: dict[str, list] = {"mail": [], "todo": [], "score": []}

    def mail_aff(_cn, names):
        calls["mail"].append(list(names))
        return [(n, {"id": i}) for i, n in enumerate(names, 1)]

    def todo_aff(_cn, names, status=""):
        calls["todo"].append(list(names))
        return [(n, {"id": i}) for i, n in enumerate(names, 1)]

    def score_aff(_cn, names):
        calls["score"].append(list(names))
        return [(n, {"id": i}) for i, n in enumerate(names, 1)]

    monkeypatch.setattr(floor.rec_mail, "list_rosters", mail_aff)
    monkeypatch.setattr(floor.rec_todo, "select_rosters", todo_aff)
    monkeypatch.setattr(floor.rec_score, "select_rosters", score_aff)
    monkeypatch.setattr(floor.rec_mail, "list_project", _boom)
    monkeypatch.setattr(floor.rec_todo, "select", _boom)
    monkeypatch.setattr(floor.rec_score, "select", _boom)
    return calls


def test_blank_names_dropped_one_in_read(monkeypatch) -> None:
    calls = _wire(monkeypatch)
    names = ["p1", "", "p2", None, "  "]
    want = [("p1", [{"id": 1}]), ("p2", [{"id": 2}])]
    assert floor._mail_by_aff(None, names) == want
    assert floor._todo_by_aff(None, names) == want
    assert floor._score_by_aff(None, names) == want
    assert calls == {"mail": [["p1", "p2"]], "todo": [["p1", "p2"]], "score": [["p1", "p2"]]}


def test_all_blank_or_empty_reads_nothing(monkeypatch) -> None:
    calls = _wire(monkeypatch)
    for names in ([], [""], ["", None], None):
        assert floor._mail_by_aff(None, names) == []
        assert floor._todo_by_aff(None, names) == []
        assert floor._score_by_aff(None, names) == []
    assert calls == {"mail": [], "todo": [], "score": []}
