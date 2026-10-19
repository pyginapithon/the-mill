"""Shared wall reads: one in-flight query, then 30 seconds of the same bytes."""

from __future__ import annotations

import threading
import time
from pathlib import Path

from fastapi.testclient import TestClient

from agent_coord.lib.observe import parse_roots
from agent_coord.server.asgi import make_asgi_app
from agent_coord.server.middleware import _FLOOR_CAP, _FLOOR_TTL, cached_read
import agent_coord.server.middleware as mw


def _clear() -> None:
    mw._floor_cache.clear()
    mw._floor_flight.clear()


def test_rail_and_aggregators_keep_thirty_seconds() -> None:
    assert _FLOOR_TTL == 30.0


def test_one_producer_serves_the_waiters() -> None:
    _clear()
    started = threading.Event()
    release = threading.Event()
    calls = {"n": 0}

    def produce() -> bytes:
        calls["n"] += 1
        started.set()
        assert release.wait(2)
        return b"shared"

    out: list[tuple[bytes, bool]] = []

    def run() -> None:
        out.append(cached_read("k", produce))

    leader = threading.Thread(target=run)
    leader.start()
    assert started.wait(2)
    waiter = threading.Thread(target=run)
    waiter.start()
    time.sleep(0.05)
    release.set()
    leader.join(2)
    waiter.join(2)
    assert calls["n"] == 1
    assert [row[0] for row in out] == [b"shared", b"shared"]
    assert False in (row[1] for row in out)
    assert True in (row[1] for row in out)


def test_a_failure_is_not_stored() -> None:
    _clear()

    def boom() -> bytes:
        raise RuntimeError("down")

    try:
        cached_read("err", boom)
    except RuntimeError:
        pass
    else:
        raise AssertionError("expected the failure")
    assert "err" not in mw._floor_cache
    body, hit = cached_read("err", lambda: b"up")
    assert body == b"up" and hit is False


def test_the_map_keeps_the_newest_keys() -> None:
    _clear()
    for i in range(_FLOOR_CAP + 3):
        cached_read(f"n{i}", lambda i=i: str(i).encode())
    assert len(mw._floor_cache) == _FLOOR_CAP
    assert f"n{_FLOOR_CAP + 2}" in mw._floor_cache
    assert "n0" not in mw._floor_cache


def test_floor_and_activity_share_one_read(monkeypatch) -> None:
    monkeypatch.setattr("agent_coord.server.admin.door.mode", lambda: "path")
    monkeypatch.setattr("agent_coord.server.allow.allowed", lambda *a, **k: True)

    class _C:
        _cn = object()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr("agent_coord.server.middleware._office", lambda: _C())
    calls = {"agents": 0, "activity": 0}

    def _agents(cn, *a, **k):
        calls["agents"] += 1
        return {
            "at": "t",
            "node": "n",
            "version": "0.5.6",
            "parts": ["agents"],
            "agents": [{"id": 1, "owner": "a"}],
            "next": None,
            "fp": {"agents": "aa"},
        }

    def _timeline(cn, project, window="24h"):
        calls["activity"] += 1
        return [{"updated": "t", "type": "mail", "desk_id": 1, "owner": "a", "n": 1, "id": "x"}]

    monkeypatch.setattr("agent_coord.server.records.floor.v1_agents", _agents)
    monkeypatch.setattr("agent_coord.server.records.floor._timeline", _timeline)
    _clear()
    root = Path(__file__).resolve().parents[2]
    client = TestClient(make_asgi_app(parse_roots(cwd=root), api_only=True))
    url = "/api/v1/agents?project=demo&limit=3"
    assert client.get(url).status_code == 200
    assert client.get(url).status_code == 200
    act = "/api/activity?project=demo&window=24h&limit=1"
    assert client.get(act).status_code == 200
    assert client.get(act).status_code == 200
    assert calls == {"agents": 1, "activity": 1}
