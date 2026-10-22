"""Human wall door. The person holds a bearer. The book stores only the hash.

Directory and IAM sign-in trades an id token for that bearer. Agent calls
on /mill/v1 and /ws do not come through here.

Wall collect and desk post still use a mill invite token, not mill connect.
"""

from __future__ import annotations

import secrets
from typing import Any

from agent_coord.const import CONST_DESK
from agent_coord.client.tokens import token_hash
from agent_coord.helpers.errors import CoordError
from agent_coord.server.admin import door
from agent_coord.server.records import mail as rec_mail
from agent_coord.server.records import opened as rec_opened


def agent_call(path: str) -> bool:
    """True when this request is the agent door, not the human wall."""
    from agent_coord.client.outbound import is_mill_verb_path

    return is_mill_verb_path(path)


def _office():
    from agent_coord.server.admin.door import _db

    return _db()


def _identity(id_token: str) -> dict | None:
    from agent_coord.server.admin.door import _JWKS, _setting
    from agent_coord.server.admin.oidc import fetch_jwks, identity

    issuer = (_setting("directory_issuer") or "").strip()
    audience = (_setting("directory_client_id") or "").strip()
    raw = (id_token or "").strip()
    if not issuer or not audience or raw.count(".") != 2:
        return None
    try:
        jwks = _JWKS.get(issuer)
        if jwks is None:
            jwks = fetch_jwks(issuer)
            _JWKS[issuer] = jwks
    except Exception:
        return None
    admin = (_setting("directory_admin_group") or "ROLE_Admin").strip() or "ROLE_Admin"
    return identity(raw, issuer=issuer, audience=audience, jwks=jwks, admin_group=admin)


def allows(token: str) -> bool:
    """True when this bearer hashes to a human row."""
    raw = (token or "").strip()
    if not raw:
        return False
    cn = _office()
    if cn is None:
        return False
    try:
        from agent_coord.server.records import human as rec_human

        return bool(rec_human.open(cn, token_hash(raw)))
    except Exception:
        return False
    finally:
        try:
            cn.close()
        except Exception:
            pass


def seat(id_token: str) -> str:
    """Verify a human id token, store a new bearer hash, return the bearer.

    An agent access token does not seat a human. The id token is not returned.
    """
    who = _identity(id_token)
    if not who or not str(who.get("sub") or "").strip():
        return ""
    if str(who.get("kind") or "") == "agent":
        return ""
    bearer = secrets.token_urlsafe(24)
    roles = who.get("roles") or []
    role = str(roles[0] or "") if roles else ""
    cn = _office()
    if cn is None:
        return ""
    try:
        from agent_coord.server.records import human as rec_human

        rec_human.put(cn, token_hash(bearer), str(who["sub"]), role)
    except Exception:
        return ""
    finally:
        try:
            cn.close()
        except Exception:
            pass
    return bearer


def _project(raw: str) -> str:
    s = (raw or "").strip() or "the-mill"
    if s == "mill":
        s = "the-mill"
    return s


def redeem_collect(code: str) -> dict[str, Any]:
    token = (code or "").strip()
    if not token:
        raise CoordError("collect: invite token required")
    row = door.match_key(token)
    if not row:
        raise CoordError("collect: invite not active")
    return {
        "ok": True,
        "human": str(row.get("label") or "human"),
        "token": token,
        "agent": str(row.get("created_by") or "*"),
        "key_id": str(row.get("key_id") or ""),
    }


def _seated_desk(cn, *secrets: str) -> str:
    """Desk whose seat matches one of these secrets. Empty when none does."""
    from agent_coord.client.tokens import token_hash
    from agent_coord.server.records.join import desk_for_token_hash

    for raw in secrets:
        secret = (raw or "").strip()
        if not secret:
            continue
        try:
            desk = desk_for_token_hash(cn, token_hash(secret))
        except Exception:
            desk = ""
        if desk:
            return desk
    return ""


def desk_post(cn, data: dict[str, Any], session: str = "") -> dict[str, Any]:
    token = str(data.get("token") or "")
    who = _seated_desk(cn, session, token)
    if not who:
        if not door.check(token) and not door.check(session):
            raise CoordError("wall send: mill invite token required")
        raise CoordError("wall send: desk session required")
    action = str(data.get("action") or "").strip().lower()
    project = _project(str(data.get("project") or ""))
    named_src = str(data.get("src") or "").strip()
    if named_src and named_src != who:
        raise CoordError("wall send: sender is the seated desk")
    src = who
    if data.get("mark_read") or action == "mark_read":
        raw_ids = data.get("ids") or data.get("id") or []
        if isinstance(raw_ids, (int, str)):
            raw_ids = [raw_ids]
        named = str(data.get("desk") or data.get("reader") or "").strip()
        alt = str(data.get("dst") or "").strip()
        if (named and named != who) or (alt and alt != who):
            raise CoordError("wall send: reader is the seated desk")
        n = 0
        for mid in raw_ids:
            rec_opened.insert(cn, int(mid), who)
            n += 1
        return {"ok": True, "n": n}
    if data.get("ack_human") or action in ("ack_human", "clear_human", "clear_human_required"):
        return {"ok": True}
    body = str(data.get("body") or "").strip()
    if not body:
        raise CoordError("wall send: body required")
    from agent_coord.server.redact import redact_text

    body = redact_text(body)[0]  # a Wall post is a write path too (0.7.5)
    dst = str(data.get("dst") or "").strip()
    if not dst or dst == "*":
        raise CoordError("wall send: dest=desk (not To: human, not *)")
    rows = rec_mail.insert(cn, project, src, dst, body, dst_kind=CONST_DESK)
    mid = int(rows[0]["id"]) if rows else 0
    try:
        from agent_coord.server.mail_push import push_mail

        if mid:
            push_mail(cn, mid)
    except Exception:
        pass
    return {"ok": True, "id": mid, "src": src, "dst": dst}
