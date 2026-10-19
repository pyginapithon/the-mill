# -*- coding: utf-8 -*-
"""First /ws sets time_connect. Last socket sets time_disconnect. New connect kicks older."""
import asyncio

from agent_coord.server.push import Hub, WS_REPLACED, WS_REPLACED_REASON


def test_socket_times_follow_first_and_last(monkeypatch) -> None:
    marks: list[tuple[str, bool]] = []
    monkeypatch.setattr(
        "agent_coord.server.push._mark_join_socket",
        lambda desk, *, up: marks.append((desk, up)),
    )
    hub = Hub()

    class FakeWS:
        def __init__(self) -> None:
            self.closed: list[int] = []
            self.sent: list[str] = []

        async def send_text(self, text: str) -> None:
            self.sent.append(text)

        async def close(self, code: int = 1000) -> None:
            self.closed.append(code)

    a = FakeWS()
    b = FakeWS()
    asyncio.run(hub.add("DESK_builder", a))
    asyncio.run(hub.add("DESK_builder", b))  # kicks a; room stays occupied
    assert hub.rooms.get("DESK_builder") == {b}
    assert a.closed == [WS_REPLACED]
    assert any(WS_REPLACED_REASON in s for s in a.sent)
    hub.discard("DESK_builder", a)  # already gone
    hub.discard("DESK_builder", b)
    assert marks == [("DESK_builder", True), ("DESK_builder", False)]
    assert "DESK_builder" not in hub.rooms
