# -*- coding: utf-8 -*-
"""drain_loop + grok-bot vendor stamps wake file.

The test waits for the stamp call to return, not for the file to appear: the
writer opens the file before it writes the line, so a read on first sight
could see an empty file (flaky under load).
"""
import threading
import time

import pytest

from agent_coord.client.connectors import grok_bot
from agent_coord.server.hint_buf import HintBuf, drain_loop


@pytest.mark.parametrize("file_first", [False, True], ids=["writer", "file-before-line"])
def test_drain_calls_grok_bot_stamp(tmp_path, monkeypatch, file_first) -> None:
    monkeypatch.setattr("agent_coord.config.mill_home", lambda: tmp_path)
    monkeypatch.setenv("AGENT_COORD_VENDOR", "grok-bot")
    monkeypatch.delenv("AGENT_COORD_BOT_WAKE_URL", raising=False)
    monkeypatch.delenv("AGENT_COORD_BOT_WAKE_CMD", raising=False)
    real = grok_bot._stamp_wake
    stamped = threading.Event()
    got = {}

    def stamp(hint):
        if file_first:
            # Widen the real open-then-write window: the file exists, empty, first.
            early = tmp_path / "session" / "builder.wake.jsonl"
            early.parent.mkdir(parents=True, exist_ok=True)
            early.touch()
            time.sleep(0.3)
        got["path"] = real(hint)
        stamped.set()
        return got["path"]

    monkeypatch.setattr(grok_bot, "_stamp_wake", stamp)
    buf = HintBuf("builder", maxsize=8)
    stop = threading.Event()
    t = threading.Thread(target=drain_loop, args=(buf, stop), daemon=True)
    t.start()
    try:
        buf.put_recv({"type": "mail", "id": 42, "hint": "MAIL"})
        assert stamped.wait(timeout=30.0), "drain did not stamp wake file"
        assert got["path"] is not None, "stamp failed to write"
        assert got["path"].name.endswith(".wake.jsonl")
        body = got["path"].read_text(encoding="utf-8")
        assert '"id":42' in body.replace(" ", "")
    finally:
        stop.set()
        t.join(timeout=2.0)
