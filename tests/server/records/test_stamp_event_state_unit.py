"""stamp_event_state without MySQL: office-wide read, then per-desk fallback (#92)."""
from __future__ import annotations

from agent_coord.server.records import floor as rec_floor


def test_stamp_event_state_global_then_per_desk(monkeypatch) -> None:
    calls = []

    def fake_select(cn, desk_id=0, limit=10):
        calls.append((desk_id, limit))
        if not desk_id:
            return [
                {"type": "mail", "id": 1, "state": "sent"},
                {"type": "todo", "id": 2, "state": None},
            ]
        if desk_id == 42:
            return [{"type": "todo", "id": 3, "state": "deleted"}]
        return []

    monkeypatch.setattr(rec_floor.rec_activity, "select", fake_select)
    monkeypatch.setattr(
        rec_floor.rec_name,
        "select",
        lambda cn, include_deleted=False: [
            {"id": 42, "name": "old", "type": "desk"},
            {"id": 43, "name": "old", "type": "roster"},
        ],
    )
    rows = rec_floor.stamp_event_state(
        None,
        [
            {"id": 1, "kind": "mail", "type": "mail", "owner": "a", "owner_type": "desk"},
            {"id": 2, "kind": "todo", "type": "todo", "owner": "a", "owner_type": "desk"},
            {"id": 3, "kind": "todo", "type": "todo", "owner": "old", "owner_type": "desk"},
            {"id": 4, "kind": "join", "type": "join", "owner": "", "owner_type": ""},
        ],
    )
    assert [r["state"] for r in rows] == ["sent", None, "deleted", None]
    assert calls == [(0, rec_floor.LIST_PAGE_MAX), (42, rec_floor.SCOPE_EVENTS_LIMIT)]


def test_stamp_event_state_empty_reads_nothing(monkeypatch) -> None:
    monkeypatch.setattr(
        rec_floor.rec_activity, "select", lambda *a, **k: (_ for _ in ()).throw(AssertionError)
    )
    assert rec_floor.stamp_event_state(None, []) == []
    assert rec_floor.stamp_event_state(None, None) == []
