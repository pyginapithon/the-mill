"""Running mill from a checkout warns when that version is not the installed dist (#170)."""
from __future__ import annotations


def test_mismatch_line(monkeypatch):
    from agent_coord.install import packver

    monkeypatch.setattr(packver, "_pyproject_version", lambda: "0.6.28")
    monkeypatch.setattr("importlib.metadata.version", lambda name: "0.6.29")
    assert packver.checkout_dist_line() == "mill: imported 0.6.28 differs from installed the-mill 0.6.29"


def test_same_version_is_quiet(monkeypatch):
    from agent_coord.install import packver

    monkeypatch.setattr(packver, "_pyproject_version", lambda: "0.6.29")
    monkeypatch.setattr("importlib.metadata.version", lambda name: "0.6.29")
    assert packver.checkout_dist_line() == ""


def test_no_checkout_is_quiet(monkeypatch):
    from agent_coord.install import packver

    monkeypatch.setattr(packver, "_pyproject_version", lambda: None)
    assert packver.checkout_dist_line() == ""
