"""Plan #25: peek/inbox hide dst=* unless --star."""
from __future__ import annotations

from agent_coord.client.outbound.addressing import inbox_dst_boxes


def test_inbox_dst_boxes_default_hides_star() -> None:
    boxes = inbox_dst_boxes("the-mill", "build-presence", role="builder")
    assert "*" not in boxes
    assert "build-presence" in boxes
    assert "builder" in boxes
    assert "the-mill" in boxes
    assert "the-mill:builder" in boxes
    assert "desk.build-presence" not in boxes
    assert "ROLE_builder" not in boxes
    assert "PROJ_the-mill" not in boxes


def test_inbox_dst_boxes_star_opt_in() -> None:
    boxes = inbox_dst_boxes("the-mill", "build-presence", role="builder", include_star=True)
    assert "*" in boxes


def test_default_boxes_do_not_inflate_with_star() -> None:
    plain = set(inbox_dst_boxes("the-mill", "desk-a", role="builder"))
    starred = set(inbox_dst_boxes("the-mill", "desk-a", role="builder", include_star=True))
    assert "*" not in plain
    assert starred - plain == {"*"}


def test_mail_listing_boxes_include_desk_role_star_product() -> None:
    boxes = inbox_dst_boxes(
        "the-mill", "build-presence", role="builder", include_star=True, include_product=True
    )
    assert "build-presence" in boxes
    assert "builder" in boxes
    assert "the-mill:builder" in boxes
    assert "*" in boxes
    assert "the-mill" in boxes
    assert "PROJ_the-mill" not in boxes
    assert "ROLE_builder" not in boxes
    assert "product.PROJ_the-mill" not in boxes
    assert "desk.build-presence" not in boxes


def test_send_star_warns_without_broadcast() -> None:
    """Pure addressing: * is star kind. Coord.send warn is tested when DB exists."""
    from agent_coord.client.outbound.addressing import parse_mail_to

    addrs = parse_mail_to("*")
    assert addrs == [{"kind": "star", "dst": "*"}]
    mixed = parse_mail_to("builder,*")
    kinds = {a["kind"] for a in mixed}
    # 0.7.0: no hardcoded role names. A bare word is a desk; the server falls back to a roster.
    assert kinds == {"star", "desk"}
