"""#652: an invite door fails closed when the key board cannot be read.

A revoked or expired key whose digest still equals the legacy door.hash must not open
the door while the book is down or the board query raises. The legacy hash still opens
for a token the board answers it does not know.
"""
from __future__ import annotations

import pytest

from agent_coord.server.admin import door

TOKEN = "inv-652-placeholder"


class _Cur:
    def __init__(self, row, boom):
        self._row, self._boom = row, boom

    def execute(self, *a, **k):
        if self._boom:
            raise RuntimeError("query failed")

    def fetchone(self):
        return self._row

    def close(self):
        pass


class _Cn:
    def __init__(self, row=None, boom=False):
        self._row, self._boom = row, boom

    def cursor(self, dictionary=False):
        return _Cur(self._row, self._boom)

    def close(self):
        pass


@pytest.fixture
def invite_door(tmp_path, monkeypatch):
    hp = tmp_path / "door.hash"
    hp.write_text(door._digest(TOKEN) + "\n", encoding="utf-8")
    monkeypatch.setattr(door, "mode", lambda: "invite")
    monkeypatch.setattr(door, "hash_path", lambda: hp)
    return hp


def test_book_unreachable_revoked_key_matching_hash_is_refused(invite_door, monkeypatch):
    monkeypatch.setattr(door, "_db", lambda: None)
    assert door.check(TOKEN) is False


def test_board_query_raises_revoked_key_matching_hash_is_refused(invite_door, monkeypatch):
    monkeypatch.setattr(door, "_db", lambda: _Cn(boom=True))
    assert door.check(TOKEN) is False


def test_revoked_row_on_readable_board_is_refused(invite_door, monkeypatch):
    row = {"revoked_at": "2026-10-22 00:00:00", "enabled_at": "2026-10-21 00:00:00", "expires_at": None}
    monkeypatch.setattr(door, "_db", lambda: _Cn(row=row))
    assert door.check(TOKEN) is False


def test_legacy_hash_still_opens_when_board_reads_and_token_unknown(invite_door, monkeypatch):
    monkeypatch.setattr(door, "_db", lambda: _Cn(row=None))
    assert door.check(TOKEN) is True
    assert door.check("some-other-token") is False


def test_board_lookup_is_three_state(monkeypatch):
    monkeypatch.setattr(door, "_db", lambda: None)
    assert door._board_knows_token(TOKEN) is None
    monkeypatch.setattr(door, "_db", lambda: _Cn(boom=True))
    assert door._board_knows_token(TOKEN) is None
    monkeypatch.setattr(door, "_db", lambda: _Cn(row=None))
    assert door._board_knows_token(TOKEN) is False
    monkeypatch.setattr(door, "_db", lambda: _Cn(row=(1,)))
    assert door._board_knows_token(TOKEN) is True


def test_directory_issuer_check_unchanged(monkeypatch):
    # The fix touches only the invite branch: a directory office with an issuer still asks allows().
    seen = []
    monkeypatch.setattr(door, "mode", lambda: "directory")
    monkeypatch.setattr(door, "_setting", lambda k: "https://issuer.example" if k == "directory_issuer" else "")
    monkeypatch.setattr("agent_coord.server.admin.human.allows", lambda t: seen.append(t) or False)
    monkeypatch.setattr(door, "_db", lambda: None)
    assert door.check(TOKEN) is False
    assert seen == [TOKEN]
