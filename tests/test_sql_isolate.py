"""Throwaway SQL DB names isolate concurrent pytest processes."""
from __future__ import annotations

import os

from tests.sql_isolate import throwaway_db


def test_throwaway_db_differs_by_pid(monkeypatch):
    monkeypatch.delenv("PYTEST_XDIST_WORKER", raising=False)
    monkeypatch.setattr(os, "getpid", lambda: 1111)
    a = throwaway_db()
    monkeypatch.setattr(os, "getpid", lambda: 2222)
    b = throwaway_db()
    assert a == "mill_records_test_1111"
    assert b == "mill_records_test_2222"
    assert a != b


def test_throwaway_db_uses_xdist_worker(monkeypatch):
    monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw3")
    monkeypatch.setattr(os, "getpid", lambda: 9999)
    assert throwaway_db("mill_records_test") == "mill_records_test_gw3"
    assert throwaway_db("mill_activity_life_test") == "mill_activity_life_test_gw3"


def test_throwaway_db_sanitizes_suffix(monkeypatch):
    monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw/0!")
    assert throwaway_db() == "mill_records_test_gw_0"
