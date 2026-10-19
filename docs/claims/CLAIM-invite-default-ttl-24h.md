# Claim - invite door mint default TTL 24h

Status: **RC Ready** on `claim/floor-v1-parts`. Local commit only. Not pushed. Not PyPI.

## Intent

Door invite keys should **always expire**. When Admin mints with no TTL
specified, default to **24h** (not never). Redeemed join seat `token_hash`
stays forever (no seat TTL) until `mill reset`.

## Acceptance (Host locked)

1. `mint_key` with `ttl` unset / empty / whitespace -> `ttl_seconds=86400`, `expires_at` ~ now+24h.
2. Explicit `0` / `never` / `none` / `-` on mint remain Admin escape (no expiry).
3. `set_key_ttl` unchanged (Admin may set any TTL including never).
4. Agent seat mint (`mint_seat` / `join.token_hash`) unchanged - no seat TTL.
5. Docs: `docs/requirements/invite.md` states mint default 24h; seat bearer has no TTL.
6. Do not change agent seat mint TTL (none).

## Evidence (path:lines)

| Piece | Where |
|---|---|
| Default const | `agent_coord/server/admin/door.py` `DEFAULT_INVITE_TTL = "24h"` |
| Mint path | `agent_coord/server/admin/door.py` `mint_key` (unset -> default) |
| parse_ttl | same file - Empty/0/never still no expiry (set_key_ttl / escape) |
| set_key_ttl | unchanged |
| Docs | `docs/requirements/invite.md` §1 table + §5 + §6 |
| Tests | `tests/install/test_invite_default_ttl.py` |

## Out of scope

- Agent `mint_seat` / seat bearer TTL
- Ban of explicit `0`/`never` (kept as Admin escape)
- Push / pack / PyPI
- wall_ui

## Self-test

```
pytest tests/install/test_invite_default_ttl.py tests/install/test_invite_admin.py -q
```

## Ready for Validator when

- Tip SHA committed locally with door mint default-24h intent
- pytest green for `test_invite_default_ttl.py` (+ existing door invite admin tests)
- Unrelated dirty left unstaged
