"""MAIL To sets: everyone | roster | roster:roster | deskId (0.7.0: one roster type)."""
from __future__ import annotations

from agent_coord.client.outbound.addressing import inbox_dst_boxes, mail_addr_kind, parse_mail_to


def test_parse_four_sets() -> None:
    rows = parse_mail_to(
        "*,the-mill,the-mill:builder,build-presence",
        project_id="the-mill",
    )
    assert [r["kind"] for r in rows] == ["star", "roster", "roster", "desk"]
    assert [r["dst"] for r in rows] == ["*", "the-mill", "builder", "build-presence"]


def test_parse_rejects_dotted_spellings() -> None:
    rows = parse_mail_to(
        "product.the-mill,role.builder,desk.build-presence",
        project_id="the-mill",
    )
    assert {r["kind"] for r in rows} == {"desk"}
    assert {r["dst"] for r in rows} == {
        "product.the-mill",
        "role.builder",
        "desk.build-presence",
    }


def test_parse_bare_word_is_desk_no_hardcoded_roles() -> None:
    rows = parse_mail_to("builder", project_id="the-mill")
    assert rows == [{"kind": "desk", "dst": "builder"}]


def test_mail_addr_kind_project_role() -> None:
    assert mail_addr_kind("*") == "star"
    assert mail_addr_kind("the-mill:builder") == "roster"
    assert mail_addr_kind("the-mill") == "desk"
    assert mail_addr_kind("product.the-mill") == "desk"
    assert mail_addr_kind("build-presence") == "desk"
    assert mail_addr_kind("builder") == "desk"


def test_inbox_four_sets() -> None:
    boxes = inbox_dst_boxes(
        "the-mill", "build-presence", role="builder", include_star=True
    )
    for need in ("*", "the-mill", "the-mill:builder", "build-presence", "builder"):
        assert need in boxes
    assert "PROJ_the-mill" not in boxes
    assert "DESK_build-presence" not in boxes
    assert "ROLE_builder" not in boxes
    assert "desk.build-presence" not in boxes
