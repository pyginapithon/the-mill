"""Unit tests for agent_coord.protocol.mail pure helpers (no MySQL).

Path A slice: coord-extract-mail. Table-driven; covers every extracted symbol.
"""
from __future__ import annotations

import pytest

from agent_coord import CoordError
from agent_coord.protocol.mail import (
    DEAD_LETTER_DST,
    MAIL_TTL_DEAD_DESK_S,
    MAIL_TTL_HUMAN_S,
    MAIL_TTL_PRODUCT_S,
    MAIL_TTL_READ_S,
    MAIL_TTL_ROLE_S,
    MAIL_TTL_STAR_S,
    expand_mail_filter_keys,
    flatten_mail_keys,
    format_read_who,
    mail_addr_kind,
    normalize_read_party,
    parse_mail_to,
)
from agent_coord.protocol import mail as mail_pkg
from agent_coord.protocol.mail import (
    expand_mail_filter_keys as expand_from_pkg,
    flatten_mail_keys as flatten_from_pkg,
    format_read_who as format_from_pkg,
    mail_addr_kind as kind_from_pkg,
    normalize_read_party as norm_from_pkg,
    parse_mail_to as parse_from_pkg,
)


@pytest.mark.parametrize(
    "raw, kinds, dsts",
    [
        ("validator", ["desk"], ["validator"]),
        ("role.builder", ["desk"], ["role.builder"]),
        ("desk.setter-upper", ["desk"], ["desk.setter-upper"]),
        ("desk.val-1", ["desk"], ["desk.val-1"]),
        ("product.mill", ["desk"], ["product.mill"]),
        ("*", ["star"], ["*"]),
        (
            "validator,desk.val-1,product.mill,*",
            ["desk", "desk", "desk", "star"],
            ["validator", "desk.val-1", "product.mill", "*"],
        ),
        ("builder,builder", ["desk"], ["builder"]),  # dedupe
    ],
)
def test_parse_mail_to_table(raw, kinds, dsts):
    rows = parse_mail_to(raw)
    assert [r["kind"] for r in rows] == kinds
    assert [r["dst"] for r in rows] == dsts
    assert parse_from_pkg(raw) == rows


@pytest.mark.parametrize("bad", ["", "   ", "setter-upper", "human"])
def test_parse_mail_to_rejects(bad):
    with pytest.raises(CoordError):
        parse_mail_to(bad)


@pytest.mark.parametrize(
    "dst, kind",
    [
        ("*", "star"),
        ("desk.val-1", "desk"),
        ("product.mill", "desk"),
        ("role.builder", "desk"),
        ("desk.setter-upper", "desk"),
        (DEAD_LETTER_DST, "dead"),
        ("setter-upper", "human"),
        ("human", "human"),
        ("builder", "desk"),
        ("validator", "desk"),
        ("auditor", "desk"),
        ("coord", "desk"),
        ("val-a", "desk"),
    ],
)
def test_mail_addr_kind_table(dst, kind):
    assert mail_addr_kind(dst) == kind
    assert kind_from_pkg(dst) == kind


@pytest.mark.parametrize(
    "vals, expect",
    [
        (None, []),
        ("", []),
        ("a", ["a"]),
        ("a,b, a", ["a", "b"]),
        (["a,b", "b", "c"], ["a", "b", "c"]),
        (("x", "y,x"), ["x", "y"]),
        (["  ", ",,"], []),
    ],
)
def test_flatten_mail_keys_table(vals, expect):
    assert flatten_mail_keys(vals) == expect
    assert flatten_from_pkg(vals) == expect


@pytest.mark.parametrize(
    "keys, expect",
    [
        (None, set()),
        ([], set()),
        (["*"], {"*"}),
        ([DEAD_LETTER_DST], {DEAD_LETTER_DST}),
        (["product.mill"], {"product.mill"}),
        (["role.builder"], {"role.builder"}),
        (["desk.val-1"], {"desk.val-1"}),
        (["setter-upper"], {"setter-upper"}),
        (["setter-upper", "role.validator"], {"setter-upper", "role.validator"}),
    ],
)
def test_expand_mail_filter_keys_table(keys, expect):
    assert expand_mail_filter_keys(keys) == expect
    assert expand_from_pkg(keys) == expect


@pytest.mark.parametrize(
    "desk, party, vendor, expect",
    [
        ("validator", "human", "", "validator:human"),
        ("builder", "agent", "", "builder:agent"),
        ("builder", "agent", "grok", "builder:agent:grok"),
        ("  desk  ", "HUMAN", "  Claude  ", "desk:human"),
        ("x", "agent", "GROK", "x:agent:grok"),
    ],
)
def test_format_read_who_table(desk, party, vendor, expect):
    assert format_read_who(desk, party, vendor) == expect
    assert format_from_pkg(desk, party, vendor) == expect


@pytest.mark.parametrize(
    "party, expect",
    [
        (None, "agent"),
        ("", "agent"),
        ("agent", "agent"),
        ("AGENT", "agent"),
        ("human", "human"),
        (" Human ", "human"),
    ],
)
def test_normalize_read_party_ok(party, expect):
    assert normalize_read_party(party) == expect
    assert norm_from_pkg(party) == expect


@pytest.mark.parametrize("bad", ["robot", "both", "desk"])
def test_normalize_read_party_rejects(bad):
    with pytest.raises(CoordError):
        normalize_read_party(bad)


def test_constants_reexported():
    assert DEAD_LETTER_DST == "dead-letter"
    assert MAIL_TTL_READ_S == 7 * 86400
    assert MAIL_TTL_DEAD_DESK_S == 3 * 86400
    assert MAIL_TTL_ROLE_S == 30 * 86400
    assert MAIL_TTL_HUMAN_S == 90 * 86400
    assert MAIL_TTL_PRODUCT_S == 30 * 86400
    assert MAIL_TTL_STAR_S == 2 * 86400
    assert mail_pkg.DEAD_LETTER_DST == DEAD_LETTER_DST
    assert mail_pkg.MAIL_TTL_READ_S == MAIL_TTL_READ_S


def test_coord_and_pkg_same_callables():
    assert parse_mail_to is parse_from_pkg
    assert mail_addr_kind is kind_from_pkg
    assert flatten_mail_keys is flatten_from_pkg
    assert expand_mail_filter_keys is expand_from_pkg
    assert format_read_who is format_from_pkg
    assert normalize_read_party is norm_from_pkg
