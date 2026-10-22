"""#670 a connect sync that replays a backlog prints no line per skipped item.
grok-bot's first wake printed ~80 identical {'watch': 'skip', ..., 'route':
'hold:HOLD'} lines: the sync handed over dozens of HOLD hints for one hold, all
with the same poke key, so every frame after the first was a duplicate and its
skip was printed. The sync line already shows the items, and a replay is never
reprinted (#618), so a replay walks each poke key once (the latest frame) and a
replayed skip logs but does not print. Row F-replay-quiet."""
from __future__ import annotations

import threading
import time

from agent_coord.client import dispatch
from agent_coord.server import hint_buf


def _hold_backlog(n: int) -> list[dict]:
    rows = [
        {"kind": "hint", "type": "hold", "id": 78, "hint": "HOLD", "detail": f"change {i}",
         "outcome": "missed", "time": f"2026-10-{6 + i % 15:02d} 00:00:00"}
        for i in range(n)
    ]
    rows.append({"kind": "hint", "type": "todo", "id": 9, "hint": "TODO", "outcome": "missed"})
    return rows


def test_a_replay_walks_each_poke_key_once_the_latest_frame():
    items = dispatch.replay_items("away", _hold_backlog(80))
    assert [(i["type"], i["id"]) for i in items] == [("hold", 78), ("todo", 9)]
    assert items[0]["detail"] == "change 79"  # the latest change of that hold
    assert items[0]["idem"] == "hint:hold:78:away"


def test_letters_keep_one_item_each():
    rows = [{"kind": "mail", "id": n, "outcome": "missed"} for n in (1, 2, 3)]
    assert [i["id"] for i in dispatch.replay_items("away", rows)] == [1, 2, 3]


def test_a_connect_sync_backlog_prints_no_skip_lines(tmp_path, monkeypatch, capsys):
    """The client path end to end: sync rows -> HintBuf -> drain loop. Nothing a
    route takes, so the hold is left for the reader; the duplicates never print."""
    monkeypatch.setattr(hint_buf, "hint_path", lambda desk: tmp_path / "h.jsonl")
    monkeypatch.setattr(dispatch, "_SEEN", set())
    monkeypatch.setattr("agent_coord.client.route_chain.try_route", lambda desk, frame: "next")
    buf = hint_buf.HintBuf("away")
    for item in dispatch.replay_items("away", _hold_backlog(80)):
        buf.put_recv(item)
    stop = threading.Event()
    t = threading.Thread(target=hint_buf.drain_loop, args=(buf, stop), daemon=True)
    t.start()
    deadline = time.time() + 5
    while not buf.q.empty() and time.time() < deadline:
        time.sleep(0.05)
    time.sleep(0.3)
    stop.set()
    t.join(2)
    out = capsys.readouterr().out
    assert "'watch': 'skip'" not in out
    assert out.count("\n") == 0


def test_a_replayed_skip_does_not_print(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(hint_buf, "hint_path", lambda desk: tmp_path / "h.jsonl")
    monkeypatch.setattr(dispatch, "dispatch_hint", lambda desk, frame, replay=False: "skip")
    buf = hint_buf.HintBuf("away")
    hint_buf._drain_one(buf, {"type": "hold", "id": 78, "hint": "HOLD", "route": "hold:HOLD"}, "HOLD",
                        time.perf_counter(), replay=True)
    assert capsys.readouterr().out == ""
    # a live skip still answers the HINT line it follows
    hint_buf._drain_one(buf, {"type": "hold", "id": 78, "hint": "HOLD", "route": "hold:HOLD"}, "HOLD",
                        time.perf_counter(), replay=False)
    assert "'watch': 'skip'" in capsys.readouterr().out
