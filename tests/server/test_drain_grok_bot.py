# -*- coding: utf-8 -*-
"""drain_loop + grok-bot vendor stamps wake file."""
import threading
import time

from agent_coord.server.hint_buf import HintBuf, drain_loop


def test_drain_calls_grok_bot_stamp(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("agent_coord.config.mill_home", lambda: tmp_path)
    monkeypatch.setenv("AGENT_COORD_VENDOR", "grok-bot")
    monkeypatch.delenv("AGENT_COORD_BOT_WAKE_URL", raising=False)
    monkeypatch.delenv("AGENT_COORD_BOT_WAKE_CMD", raising=False)
    buf = HintBuf("builder", maxsize=8)
    stop = threading.Event()
    t = threading.Thread(target=drain_loop, args=(buf, stop), daemon=True)
    t.start()
    try:
        buf.put_recv({"type": "mail", "id": 42, "hint": "MAIL"})
        wakes = []
        for _ in range(40):
            wakes = list((tmp_path / "session").glob("*.wake.jsonl"))
            if wakes:
                break
            time.sleep(0.05)
        assert wakes, "drain did not stamp wake file"
        body = wakes[0].read_text(encoding="utf-8")
        assert '"id":42' in body.replace(" ", "")
    finally:
        stop.set()
        t.join(timeout=2.0)
