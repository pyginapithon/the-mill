# -*- coding: utf-8 -*-
"""drain_loop: handler runs while the desk is busy, and the next HINT is not stuck behind it."""
import json
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

from agent_coord.client.route_chain import save_routes
from agent_coord.server.hint_buf import HintBuf, drain_loop


def _write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def test_drain_handler_gets_detail_without_blocking(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("agent_coord.config.mill_home", lambda: tmp_path)
    monkeypatch.setenv("AGENT_COORD_VENDOR", "grok-build")
    monkeypatch.delenv("AGENT_COORD_SPAWN", raising=False)
    monkeypatch.delenv("AGENT_COORD_BOT_WAKE_CMD", raising=False)
    monkeypatch.delenv("AGENT_COORD_BOT_WAKE_URL", raising=False)

    pidfile = tmp_path / "slow.pid"
    marker = tmp_path / "fast.txt"
    slow = tmp_path / "slow.py"
    fast = tmp_path / "fast.py"
    _write(
        slow,
        "import os, sys, time\n"
        "from pathlib import Path\n"
        "Path(sys.argv[1]).write_text(str(os.getpid()), encoding='utf-8')\n"
        "time.sleep(60)\n",
    )
    _write(
        fast,
        "import sys\n"
        "from pathlib import Path\n"
        "Path(sys.argv[1]).write_text(sys.stdin.read(), encoding='utf-8')\n",
    )
    save_routes(
        "builder",
        {
            "mail:MAIL": subprocess.list2cmdline([sys.executable, str(slow), str(pidfile)]),
            "todo:TODO": subprocess.list2cmdline([sys.executable, str(fast), str(marker)]),
        },
    )
    buf = HintBuf("builder", maxsize=8)
    stop = threading.Event()
    t = threading.Thread(target=drain_loop, args=(buf, stop), daemon=True)
    t.start()
    slow_pid = 0
    try:
        buf.put_recv(
            {
                "type": "mail",
                "id": 1,
                "hint": "MAIL",
                "detail": "slow",
                "token": "sekret",
            }
        )
        buf.put_recv(
            {
                "type": "todo",
                "id": 9,
                "hint": "TODO",
                "detail": "need,status",
                "authorization": "Bearer abc",
            }
        )
        deadline = time.time() + 8
        while time.time() < deadline and not marker.is_file():
            time.sleep(0.05)
        assert marker.is_file(), "fast handler did not run while slow handler was still up"
        body = json.loads(marker.read_text(encoding="utf-8"))
        assert body["detail"] == "need,status"
        assert body["id"] == 9
        assert "authorization" not in body
        assert "token" not in body
        assert pidfile.is_file()
        slow_pid = int(pidfile.read_text(encoding="utf-8").strip())
    finally:
        stop.set()
        t.join(timeout=2.0)
        if slow_pid:
            try:
                os.kill(slow_pid, signal.SIGTERM)
            except OSError:
                pass
