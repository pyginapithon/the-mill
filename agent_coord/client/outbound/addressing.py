"""Mail To: parse and addr_kind (pure; no DB)."""
from __future__ import annotations


from agent_coord.const import CONST_DESK, CONST_ROSTER


def parse_mail_to(raw: str, *, project_id: str = "") -> list[dict[str, str]]:
    """Parse send To: tokens. Comma = multi-To.

    To sets:
      *                      -> everyone on the letter project
      the-mill               -> that project mailbox when it is the letter project
      the-mill:builders      -> roster builders
      build-presence         -> desk (the server falls back to a live roster of that name)
    A bare human badge is not a To target. No hardcoded role names (0.7.0).
    """
    from agent_coord.helpers.errors import CoordError
    from agent_coord.helpers.ident import STABLE_HUMANS, slug

    s = (raw or "").strip()
    if not s:
        raise CoordError("send: To required")
    pid = slug(project_id) if (project_id or "").strip() else ""
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for part in s.split(","):
        tok = part.strip()
        if not tok:
            continue
        if tok == "*":
            kind, dst = "star", "*"
        elif ":" in tok:
            left, right = tok.split(":", 1)
            slug(left)
            kind, dst = CONST_ROSTER, slug(right)
        else:
            bare = slug(tok)
            if bare in STABLE_HUMANS:
                raise CoordError(
                    f"send: To {bare!r} is a human badge, not a desk/role mailbox; "
                    "use a desk id (owner) or role"
                )
            if pid and bare == pid:
                kind, dst = CONST_ROSTER, bare
            else:
                kind, dst = "desk", bare
        if dst in seen:
            continue
        seen.add(dst)
        out.append({"kind": kind, "dst": dst})
    if not out:
        raise CoordError("send: To required")
    return out


def inbox_dst_boxes(
    project_id: str,
    desk: str,
    *,
    role: str = "",
    include_star: bool = False,
    include_product: bool = True,
) -> list[str]:
    """MAIL boxes: desk name + project + project:role + optional * everyone."""
    from agent_coord.helpers.ident import slug

    pid = slug(project_id) if (project_id or "").strip() else ""
    who = (desk or "").strip()
    boxes: set[str] = set()
    if who:
        boxes.add(who)
    role_s = (role or "").strip()
    if role_s:
        role_s = slug(role_s)
        boxes.add(role_s)
        if pid:
            boxes.add(f"{pid}:{role_s}")
    if include_star:
        boxes.add("*")
    if include_product and pid:
        boxes.add(pid)
    return sorted(boxes)


def mail_addr_kind(dst: str) -> str:
    from agent_coord.helpers.ident import STABLE_HUMANS
    from agent_coord.protocol.mail.constants import DEAD_LETTER_DST

    d = (dst or "").strip()
    if d == "*":
        return "star"
    if ":" in d:
        return CONST_ROSTER
    if d == DEAD_LETTER_DST:
        return "dead"
    if d in STABLE_HUMANS:
        return "human"
    return CONST_DESK


def _json_literal_token(tok: str) -> bool:
    """True for JSON tokens that were never quoted (true/false/null/numbers)."""
    import json

    if tok in ("true", "false", "null"):
        return True
    try:
        json.loads(tok)
    except json.JSONDecodeError:
        return False
    return True


def _requote_powershell_stripped(s: str) -> str:
    """Restore quotes PowerShell 5 strips from a native argv JSON array.

    ``[{deskId:grok-tui}]`` and ``[grok-tui]`` become JSON. Brackets, commas,
    colons, whitespace, and unquoted JSON literals stay as they were. A quote
    that survived (backslash-escaped on the command line) is copied through.
    """
    import json

    structural = set("{}[],:")
    out: list[str] = []
    i = 0
    n = len(s)
    while i < n:
        c = s[i]
        if c == '"':
            j = i + 1
            while j < n:
                if s[j] == "\\" and j + 1 < n:
                    j += 2
                    continue
                if s[j] == '"':
                    j += 1
                    break
                j += 1
            else:
                raise json.JSONDecodeError("unterminated string", s, i)
            out.append(s[i:j])
            i = j
            continue
        if c in structural or c.isspace():
            out.append(c)
            i += 1
            continue
        j = i
        while j < n and s[j] not in structural and not s[j].isspace() and s[j] != '"':
            j += 1
        tok = s[i:j]
        out.append(tok if _json_literal_token(tok) else json.dumps(tok))
        i = j
    return "".join(out)


def parse_mail_to_cli_json(raw: str) -> list[dict]:
    """Parse --mail-to into [{deskId, roster?}...].

    One argv string. Real JSON, including the PowerShell form whose quotes
    were backslash-escaped and therefore survived, goes through json.loads.
    On JSONDecodeError, a quote-stripped array (``[{deskId:grok-tui}]``,
    ``[grok-tui]``) is re-quoted and parsed. A bare desk or comma-separated
    desks are accepted too. Raises CoordError on a bad shape.
    """
    import json

    from agent_coord.helpers.errors import CoordError

    s = (raw or "").strip()
    if not s:
        return []
    try:
        data = json.loads(s)
    except json.JSONDecodeError as first_err:
        data = None
        if s.startswith("["):
            try:
                data = json.loads(_requote_powershell_stripped(s))
            except json.JSONDecodeError:
                data = None
        elif not s.startswith("{"):
            parts = [p.strip() for p in s.split(",") if p.strip()]
            if parts and not any(ch in p for p in parts for ch in "[]{}"):
                data = [{"deskId": p} for p in parts]
        if data is None:
            raise CoordError(
                "mail-to: need one argv JSON array "
                "(PowerShell: quote --mail-to value as one string)"
            ) from first_err
    if not isinstance(data, list):
        raise CoordError("mail-to: JSON must be an array of {deskId, roster?}")
    out: list[dict] = []
    for item in data:
        if isinstance(item, str):
            desk = item.strip()
            if not desk:
                raise CoordError("mail-to: empty deskId string")
            out.append({"deskId": desk})
            continue
        if not isinstance(item, dict):
            raise CoordError("mail-to: items must be deskId or {deskId, roster?}")
        desk_raw = item.get("deskId") or item.get("desk") or item.get("dst") or ""
        desk = str(desk_raw or "").strip()
        if not desk:
            raise CoordError("mail-to: entry needs deskId")
        row: dict = {"deskId": desk}
        if "roster" in item:
            row["roster"] = item.get("roster")
        out.append(row)
    return out
