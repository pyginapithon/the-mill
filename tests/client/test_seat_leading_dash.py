"""A seat value may start with '-' (#145)."""
from __future__ import annotations

from agent_coord.__main__ import normalize_seat_argv
from agent_coord.server.admin.seats import mint_seat_secret


def test_normalize_joins_a_leading_dash_onto_seat():
    got = normalize_seat_argv(["join", "https://office.example/", "--seat", "-abc", "--desk", "grok-tui"])
    assert got == ["join", "https://office.example/", "--seat=-abc", "--desk", "grok-tui"]


def test_normalize_leaves_a_real_flag_alone():
    got = normalize_seat_argv(["join", "--seat", "--desk", "grok-tui"])
    assert got == ["join", "--seat", "--desk", "grok-tui"]


def test_mint_never_starts_with_a_dash():
    for _ in range(40):
        seat = mint_seat_secret()
        assert seat
        assert not seat.startswith("-")
        seat.encode("ascii")
