"""#488 mill briefing spawn must resolve spawn.md."""
from __future__ import annotations

from agent_coord.install.office import briefing_text


def test_briefing_spawn_reads_file():
    text = briefing_text("spawn")
    assert "spawn" in text.lower()
    assert "HINT" in text or "connect" in text.lower()
