# mill-wall MySQL + token check. Not leftover Coord commands.
from __future__ import annotations

from typing import Any

from agent_coord.client.tokens import read_session_token, token_hash
from agent_coord.helpers.errors import CoordError
from agent_coord.helpers.ident import slug
from agent_coord.server.records.db import connect


class Book:
    """One mill dest connection for mill-wall HTTP /ws."""

    def __init__(self, **override):
        self._tokens: dict[tuple[str, str], str] = {}
        self._cn = connect()

    def close(self) -> None:
        try:
            self._cn.close()
        except Exception:
            pass

    def __enter__(self) -> Book:
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def _token_plain(self, project_id: str, owner: str, token: str | None = None) -> str | None:
        t = (
            (token or "").strip()
            or self._tokens.get((project_id, owner), "")
            or (read_session_token(owner) or "")
        )
        return t or None


    def resolve_bearer(self, token: str) -> str:
        """Desk name whose join.token_hash matches Bearer. Empty if unknown."""
        from agent_coord.client.tokens import token_hash
        from agent_coord.server.records import join as rec_join

        plain = (token or "").strip()
        if not plain:
            return ""
        return rec_join.desk_for_token_hash(self._cn, token_hash(plain))

    def _guard_owner(
        self, project_id: str, owner: str, token: str | None = None, *, must_be_present: bool = False
    ) -> dict[str, Any] | None:
        from agent_coord.server.records import join as rec_join

        from agent_coord.client.session_errors import SESSION_INVALID_REJOIN

        want = (owner or "").strip()
        stored = rec_join.token_hash_for_desk(self._cn, want)
        if stored is None:
            if must_be_present:
                raise CoordError(SESSION_INVALID_REJOIN)
            return None
        plain = self._token_plain(project_id, owner, token)
        if not plain:
            raise CoordError(SESSION_INVALID_REJOIN)
        digest = token_hash(plain)
        if not stored or stored != digest:
            # Hash cleared / reminted elsewhere / stale local file
            raise CoordError(SESSION_INVALID_REJOIN)
        return {"desk": want}
