"""Admin membership on the book. Not ~/.mill/admins."""
from __future__ import annotations

from agent_coord.const import CONST_ADMIN, CONST_ROSTER
from agent_coord.helpers.errors import CoordError
from agent_coord.server.records import member as rec_member


# Set by the wall from the socket peer. A client body cannot set this.
_LOOPBACK = frozenset({"127.0.0.1", "::1", "localhost", "::ffff:127.0.0.1"})


def mark_host(data: dict, peer: str) -> None:
    data.pop("host", None)
    if (peer or "") in _LOOPBACK:
        data["host"] = True


def _desk(value) -> str:
    return str(value or "").strip()


def role_admin_any(cn) -> bool:
    return any(True for _ in rec_member.select(cn, CONST_ADMIN, "", CONST_ROSTER))


def is_role_admin(cn, desk: str) -> bool:
    """Is this desk a member of the Admin roster? One EXISTS read, not the member list."""
    from agent_coord.server.records.db import scalar_done

    who = _desk(desk)
    if not who:
        return False
    return (
        scalar_done(
            cn,
            "SELECT 1 FROM member m"
            " JOIN name r ON r.id = m.name_id AND r.type = %s AND r.name = %s"
            " JOIN name d ON d.id = m.desk_id AND d.name = %s"
            " LIMIT 1",
            (CONST_ROSTER, CONST_ADMIN, who),
        )
        is not None
    )


def is_human_admin(cn, bearer_hash: str) -> bool:
    """Is the signed-in human behind this bearer hash an Admin? (#sec S-4)

    True when the human's directory role maps onto the Admin roster, or a desk
    linked to that human is an Admin roster member. A bearer with no role row is
    a viewer, not an Admin. One EXISTS read.
    """
    from agent_coord.server.records.db import scalar_done

    h = (bearer_hash or "").strip()
    if not h:
        return False
    return (
        scalar_done(
            cn,
            "SELECT 1 FROM human h"
            " JOIN name r ON r.type = %s AND r.name = %s"
            " WHERE h.bearer_hash = %s AND ("
            "  EXISTS (SELECT 1 FROM human_member hm"
            "   WHERE hm.human_id = h.id AND hm.name_id = r.id)"
            "  OR EXISTS (SELECT 1 FROM human_desk hd"
            "   JOIN member m ON m.desk_id = hd.desk_id AND m.name_id = r.id"
            "   WHERE hd.human_id = h.id))"
            " LIMIT 1",
            (CONST_ROSTER, CONST_ADMIN, h),
        )
        is not None
    )


def require_admin(cn, desk: str) -> None:
    if not is_role_admin(cn, desk):
        raise CoordError(f"mill Admin required ({CONST_ROSTER} {CONST_ADMIN} member)")


def require_admin_if_limited(cn, desk: str) -> None:
    """High trust: any seated desk. Limited trust: Admin only."""
    from agent_coord.config import mill_trust

    if mill_trust() == "limited":
        require_admin(cn, desk)


def require_invite_seat_mint(cn, desk: str, *, human_ok: bool = False) -> None:
    """Mint one-seat agent invite URL.

    Admin always. Human badge only when trust=high.
    limited: Admin agents only (no broad human mint).
    """
    from agent_coord.config import mill_trust

    if is_role_admin(cn, desk):
        return
    if human_ok and mill_trust() == "high":
        return
    if mill_trust() == "limited":
        raise CoordError(f"limited-trust: mint_seat needs {CONST_ROSTER} {CONST_ADMIN}")
    raise CoordError(f"mint_seat: {CONST_ROSTER} {CONST_ADMIN} or (trust=high) human badge")
