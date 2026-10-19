"""#487 mill todo need peek filters the board."""
from __future__ import annotations

from unittest.mock import MagicMock

from agent_coord.server.api.mill import rpc


def test_todo_filters_by_need(monkeypatch):
    rows = [
        {"id": 1, "status": "open", "body": "slug=alpha\ndoing=\ndetail=a", "assigned_id": None, "creator_id": None},
        {"id": 2, "status": "open", "body": "slug=beta\ndoing=\ndetail=b", "assigned_id": None, "creator_id": None},
    ]

    def fake_page(cn, project, status="", *, hide_done=False, card_id=0):
        return rows

    def fake_unpack(body, tid):
        slug = "alpha" if "alpha" in (body or "") else "beta"
        return {"need_id": slug, "doing": "", "detail": slug, "progress": ""}

    monkeypatch.setattr("agent_coord.server.records.todo.page", fake_page)
    monkeypatch.setattr("agent_coord.server.records.todo.unpack", fake_unpack)
    monkeypatch.setattr("agent_coord.server.records.name.by_id", lambda *a, **k: None)

    book = MagicMock()
    all_rows = rpc._h_todo(book, {}, "PROJ_the-mill", "DESK_builder")
    assert len(all_rows) == 2
    one = rpc._h_todo(book, {"need": "beta"}, "PROJ_the-mill", "DESK_builder")
    assert len(one) == 1
    assert one[0]["need_id"] == "beta"
