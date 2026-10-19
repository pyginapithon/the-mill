"""Refused hold: top-level envelope ok matches result.ok (#207)."""
from __future__ import annotations

from agent_coord.server.asgi import hold_envelope_ok


def test_refused_hold_envelope_ok_is_false():
    assert hold_envelope_ok("hold", {"ok": False, "held": False}) is False


def test_taken_hold_envelope_stays_true():
    assert hold_envelope_ok("hold", {"ok": True, "held": True}) is True


def test_other_verb_with_false_result_stays_true():
    assert hold_envelope_ok("pass", {"ok": False}) is True


def test_refused_drop_envelope_ok_is_false():
    assert hold_envelope_ok("drop", {"ok": False, "released": False}) is False
    assert hold_envelope_ok("drop", {"ok": True, "released": True}) is True
