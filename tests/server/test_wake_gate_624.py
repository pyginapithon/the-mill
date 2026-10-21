"""#624 the wake window (one POST per desk per WAKE_WINDOW_S) starts only when a valid
POST is attempted: a refused URL or a host that is not public takes no gate,
so it never blocks the desk's next valid wake. Row F71 (wake-gate)."""
from __future__ import annotations

from agent_coord.server import wake
from tests.server.webhook_fixtures import HOOK_HOST, HOOK_KEY, HOOK_URL, arm, opener


class _Resp:
    status = 200

    def read(self, _n: int = 0) -> bytes:
        return b""

    def __enter__(self):
        return self

    def __exit__(self, *_a) -> bool:
        return False


def _ok(calls):
    return lambda req, timeout: calls.append(req.full_url) or _Resp()


def test_a_refused_url_takes_no_gate(monkeypatch):
    table = {"d1": ("https://elsewhere.example.com/automations/webhook/x", HOOK_KEY)}
    arm(monkeypatch, armed=table)
    calls: list = []
    with opener(_ok(calls)):
        assert wake.post_desk(object(), "d1", {"kind": "hint", "id": 1}) == "error"
        assert wake.post_desk(object(), "d1", {"kind": "hint", "id": 2}) == "error"  # not coalesced
        assert "d1" not in wake._GATE
        table["d1"] = (HOOK_URL, HOOK_KEY)  # the desk re-arms with a good URL
        assert wake.post_desk(object(), "d1", {"kind": "hint", "id": 3}) == "sent"
    assert calls == [HOOK_URL]


def test_a_host_that_is_not_public_takes_no_gate(monkeypatch):
    arm(monkeypatch)
    monkeypatch.setattr(wake, "public_host", lambda host: False)
    calls: list = []
    with opener(_ok(calls)):
        assert wake.post_desk(object(), "d1", {"kind": "hint", "id": 1}) == "error"
        assert "d1" not in wake._GATE
        monkeypatch.setattr(wake, "public_host", lambda host: True)
        assert wake.post_desk(object(), "d1", {"kind": "hint", "id": 2}) == "sent"
    assert calls == [HOOK_URL]


def test_a_valid_post_still_starts_the_window(monkeypatch):
    arm(monkeypatch)
    calls: list = []
    with opener(_ok(calls)):
        assert wake.post_desk(object(), "d1", {"kind": "hint", "id": 1}) == "sent"
        assert wake.post_desk(object(), "d1", {"kind": "hint", "id": 2}) == "coalesced"
    assert calls == [HOOK_URL] and HOOK_HOST in calls[0]


def test_a_failed_valid_post_keeps_its_window(monkeypatch):
    """A POST that was attempted (and failed) still rings once per window: no retry storm."""
    arm(monkeypatch)

    def boom(req, timeout):
        raise OSError("down")

    with opener(boom):
        assert wake.post_desk(object(), "d1", {"kind": "hint", "id": 1}) == "error"
        assert wake.post_desk(object(), "d1", {"kind": "hint", "id": 2}) == "coalesced"
