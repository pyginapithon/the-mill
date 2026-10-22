"""Admin membership on the book. Not ~/.mill/admins."""
from __future__ import annotations

from agent_coord.const import CONST_ADMIN, CONST_OFFICE, CONST_ROSTER
from agent_coord.helpers.errors import CoordError
from agent_coord.server.records import member as rec_member


# Set by the wall from the socket peer. A client body cannot set this.
_LOOPBACK = frozenset({"127.0.0.1", "::1", "localhost", "::ffff:127.0.0.1"})


def mark_host(data: dict, peer: str, *, forwarded: bool = False) -> None:
    """host=True only for a direct loopback peer. A request carrying
    X-Forwarded-For came through a proxy (the nginx edge proxies from
    loopback), so it is never the office host (#730)."""
    data.pop("host", None)
    if not forwarded and (peer or "") in _LOOPBACK:
        data["host"] = True


def _desk(value) -> str:
    return str(value or "").strip()


# The reserved rosters: Office is name id 1, Admin is name id 2 (tables.sql seed).
# sp_name never deletes either and never renames Admin; an Admin may rename
# Office, so code reaches it by id 1 and treats the name Office as its alias (#722).
OFFICE_ROSTER_ID = 1
ADMIN_ROSTER_ID = 2
RESERVED_ROSTER_IDS = frozenset({OFFICE_ROSTER_ID, ADMIN_ROSTER_ID})


def reserved_roster_id(cn, name) -> int | None:
    """The id when this roster name resolves to Office or Admin, else None (#722).

    Resolved the way the book resolves it (case- and accent-insensitive).
    """
    from agent_coord.server.records.db import scalar_done

    raw = _desk(name)
    if not raw or cn is None:
        return None
    try:
        got = scalar_done(
            cn,
            "SELECT id FROM name WHERE type = %s AND name = TRIM(%s) LIMIT 1",
            (CONST_ROSTER, raw),
        )
        nid = int(got) if got is not None else None
    except Exception:
        return None
    return nid if nid in RESERVED_ROSTER_IDS else None


def office_name(cn) -> str:
    """The stored name of the Office roster (id 1), which an Admin may rename (#722).

    Falls back to the seed name when the book cannot be read.
    """
    from agent_coord.server.records.db import scalar_done

    if cn is None:
        return CONST_OFFICE
    try:
        got = scalar_done(
            cn,
            "SELECT name FROM name WHERE id = %s AND type = %s LIMIT 1",
            (OFFICE_ROSTER_ID, CONST_ROSTER),
        )
    except Exception:
        return CONST_OFFICE
    if isinstance(got, (bytes, bytearray)):
        got = got.decode("utf-8")
    # Only a real stored name counts (a stub cursor in tests returns other objects).
    return got.strip() if isinstance(got, str) and got.strip() else CONST_OFFICE


def is_office_roster(cn, name) -> bool:
    """Does this roster name mean the Office roster (id 1)? (#722)

    True for the alias Office in any spelling and for the current name of id 1.
    """
    raw = _desk(name)
    if not raw:
        return False
    if raw.casefold() == CONST_OFFICE.casefold():
        return True
    return reserved_roster_id(cn, raw) == OFFICE_ROSTER_ID


def is_admin_roster(cn, name) -> bool:
    """Does this roster name resolve to the reserved Admin roster? (#674, #675)

    The name table is case- and accent-insensitive (utf8mb4_0900_ai_ci), so a
    Python string compare against CONST_ADMIN is not enough: "admin" and other
    spellings resolve to the same row. A casefold match is refused at once; any
    other name is resolved the way the book resolves it and compared by id.
    SQL refuses the same names on its own; this check makes the refusal clean.
    """
    from agent_coord.server.records.db import scalar_done

    raw = _desk(name)
    if not raw:
        return False
    if raw.casefold() == CONST_ADMIN.casefold():
        return True
    if cn is None:
        return False
    try:
        got = scalar_done(
            cn,
            "SELECT id FROM name WHERE type = %s AND name = TRIM(%s) LIMIT 1",
            (CONST_ROSTER, raw),
        )
    except Exception:
        return False
    try:
        return got is not None and int(got) == ADMIN_ROSTER_ID
    except (TypeError, ValueError):
        return False


def role_admin_any(cn) -> bool:
    return any(True for _ in rec_member.select(cn, CONST_ADMIN, "", CONST_ROSTER))


def is_role_admin(cn, desk: str) -> bool:
    """Is this desk a member of the Admin roster (id 2, never its name: #722)? One EXISTS read."""
    from agent_coord.server.records.db import scalar_done

    who = _desk(desk)
    if not who:
        return False
    return (
        scalar_done(
            cn,
            "SELECT 1 FROM member m"
            " JOIN name d ON d.id = m.desk_id AND d.name = %s"
            " WHERE m.name_id = %s"
            " LIMIT 1",
            (who, ADMIN_ROSTER_ID),
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
            " WHERE h.bearer_hash = %s AND ("
            "  EXISTS (SELECT 1 FROM human_member hm"
            "   WHERE hm.human_id = h.id AND hm.name_id = %s)"
            "  OR EXISTS (SELECT 1 FROM human_desk hd"
            "   JOIN member m ON m.desk_id = hd.desk_id AND m.name_id = %s"
            "   WHERE hd.human_id = h.id))"
            " LIMIT 1",
            (h, ADMIN_ROSTER_ID, ADMIN_ROSTER_ID),
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
