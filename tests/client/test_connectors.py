# -*- coding: utf-8 -*-
import json
import sys
import time
from pathlib import Path

import pytest

from agent_coord.client.connectors import CONNECTORS, poke
from agent_coord.client.connectors import grok_build, grok_bot


def test_grok_build_ping_skips_stamp(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("agent_coord.config.mill_home", lambda: tmp_path)
    monkeypatch.delenv("AGENT_COORD_BOT_WAKE_URL", raising=False)
    monkeypatch.delenv("AGENT_COORD_BOT_WAKE_CMD", raising=False)
    grok_build.poke({"type": "heartbeat", "id": 0, "hint": "PING", "desk": "grok-tui"})
    assert list((tmp_path / "session").glob("*.wake.jsonl")) == []


def test_grok_build_popen_grok_dash_p(tmp_path, monkeypatch) -> None:
    seen = {}

    def fake_popen(argv, **kw):
        seen["argv"] = argv
        return None

    monkeypatch.setattr("agent_coord.config.mill_home", lambda: tmp_path)
    monkeypatch.delenv("AGENT_COORD_BOT_WAKE_URL", raising=False)
    monkeypatch.delenv("AGENT_COORD_BOT_WAKE_CMD", raising=False)
    monkeypatch.setenv("AGENT_COORD_GROK_SESSION", "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
    monkeypatch.setattr("agent_coord.client.connectors.grok_build.shutil.which", lambda n: "/bin/grok")
    monkeypatch.setattr("agent_coord.client.connectors.grok_build.subprocess.Popen", fake_popen)
    grok_build.poke({"type": "mail", "id": 14, "hint": "MAIL", "desk": "grok-tui"})
    assert seen["argv"][0] == "/bin/grok"
    assert seen["argv"][1] == "-p"
    assert seen["argv"][3] == "-r"
    assert seen["argv"][4].startswith("aaaaaaaa")


def test_grok_build_stamps_when_no_hook(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("agent_coord.config.mill_home", lambda: tmp_path)
    monkeypatch.delenv("AGENT_COORD_BOT_WAKE_URL", raising=False)
    monkeypatch.delenv("AGENT_COORD_BOT_WAKE_CMD", raising=False)
    hint = {"type": "mail", "id": 14, "hint": "MAIL", "desk": "grok-tui"}
    grok_build.poke(hint)
    wakes = list((tmp_path / "session").glob("*.wake.jsonl"))
    assert len(wakes) == 1
    assert json.loads(wakes[0].read_text(encoding="utf-8").strip())["id"] == 14


def test_grok_bot_ping_skips_stamp(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("agent_coord.config.mill_home", lambda: tmp_path)
    monkeypatch.delenv("AGENT_COORD_BOT_WAKE_URL", raising=False)
    monkeypatch.delenv("AGENT_COORD_BOT_WAKE_CMD", raising=False)
    grok_bot.poke({"type": "heartbeat", "id": 0, "hint": "PING", "desk": "builder"})
    assert list((tmp_path / "session").glob("*.wake.jsonl")) == []


def test_grok_bot_stamps_when_no_hook(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("agent_coord.config.mill_home", lambda: tmp_path)
    monkeypatch.delenv("AGENT_COORD_BOT_WAKE_URL", raising=False)
    monkeypatch.delenv("AGENT_COORD_BOT_WAKE_CMD", raising=False)
    hint = {"type": "mail", "id": 7, "hint": "MAIL", "desk": "builder"}
    grok_bot.poke(hint)
    wakes = list((tmp_path / "session").glob("*.wake.jsonl"))
    assert len(wakes) == 1
    line = wakes[0].read_text(encoding="utf-8").strip()
    assert json.loads(line)["id"] == 7


def test_grok_bot_wake_url(monkeypatch) -> None:
    seen = {}

    def fake(url, payload, timeout=2.0):
        seen["url"] = url
        seen["payload"] = payload
        return True

    monkeypatch.setenv("AGENT_COORD_BOT_WAKE_URL", "http://127.0.0.1:9/wake")
    monkeypatch.delenv("AGENT_COORD_BOT_WAKE_CMD", raising=False)
    grok_bot._dead_until = 0.0
    monkeypatch.setattr("agent_coord.server.wake.fire_wake_hook", fake)
    hint = {"type": "mail", "id": 3, "hint": "MAIL", "desk": "builder"}
    grok_bot.poke(hint)
    assert seen["url"].endswith("/wake")
    assert seen["payload"]["id"] == 3


def test_grok_bot_dead_url_does_not_wait_again(monkeypatch) -> None:
    calls = []

    def fake(url, payload, timeout=2.0):
        calls.append(timeout)
        return False

    monkeypatch.setenv("AGENT_COORD_BOT_WAKE_URL", "http://127.0.0.1:9/wake")
    monkeypatch.delenv("AGENT_COORD_BOT_WAKE_CMD", raising=False)
    grok_bot._dead_until = 0.0
    monkeypatch.setattr("agent_coord.server.wake.fire_wake_hook", fake)
    hint = {"type": "todo", "id": 1, "hint": "TODO", "desk": "builder"}
    with pytest.raises(RuntimeError):
        grok_bot.poke(hint)
    with pytest.raises(RuntimeError, match="skipped"):
        grok_bot.poke(hint)
    assert calls == [0.3]
    grok_bot._dead_until = 0.0


def test_grok_bot_wake_cmd(tmp_path, monkeypatch) -> None:
    out = tmp_path / "woke.txt"
    helper = tmp_path / "wake_helper.py"
    helper.write_text(
        "import sys\n"
        "from pathlib import Path\n"
        f"Path(r'{out}').write_text(sys.stdin.read(), encoding='utf-8')\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("AGENT_COORD_BOT_WAKE_URL", raising=False)
    monkeypatch.setenv("AGENT_COORD_BOT_WAKE_CMD", f'"{sys.executable}" "{helper}"')
    hint = {"type": "todo", "id": 9, "hint": "TODO", "desk": "builder"}
    grok_bot.poke(hint)
    for _ in range(50):
        if out.exists() and out.stat().st_size:
            break
        time.sleep(0.05)
    assert out.exists(), "wake cmd did not write"
    assert json.loads(out.read_text(encoding="utf-8"))["id"] == 9


def test_ping_does_not_spawn(monkeypatch) -> None:
    from agent_coord.client.connectors import claude

    monkeypatch.setattr(
        "agent_coord.client.connectors.spawn.spawn_cli",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("no spawn on PING")),
    )
    claude.poke({"type": "heartbeat", "id": 0, "hint": "PING"})


def test_stubs_raise_for_volunteers() -> None:
    hint = {"type": "mail", "id": 1, "hint": "MAIL"}
    with pytest.raises(NotImplementedError):
        poke("kimi", hint)
    with pytest.raises(NotImplementedError):
        poke("openai-agents", hint)
    with pytest.raises(NotImplementedError):
        poke("antigravity", hint)
    with pytest.raises(NotImplementedError):
        poke("claude", hint)
    assert set(CONNECTORS) >= {
        "grok-build",
        "grok-bot",
        "antigravity",
        "claude",
        "kimi",
        "openai-agents",
    }
