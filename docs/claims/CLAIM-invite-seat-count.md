# Claim - invite seat_count (Nest invite book totals)

Status: **RC Ready** on `claim/floor-v1-parts`. Local commit only. Not pushed. Not PyPI.

## Intent

Wall-ui Host Nest strip needs Nest invite book totals - not agent seat /
`join.token_hash` desks.

Display example: `4 (joined)/ 29 (invited)`.

## Acceptance (Host locked)

1. `POST /api/admin/invites` `{ "action":"seat_count", "owner":"<badge desk>" }` (+ token as mint requires)
2. Response `{ "ok": true, "invites": N, "joined": M }`
3. `invites` = `SELECT COUNT(*) FROM mill_invite`
4. `joined` = `SELECT COUNT(*) FROM mill_invite_join`
5. Same gate as mint: `require_invite_seat_mint` (owner/token for auth only)
6. Action name kept `seat_count` (alias `invite_count` / `count_seats` accepted)
7. Door mint bumps `invites`; `mill_invite_join` row bumps `joined`
8. Agent `mint_seat` / `join.token_hash` path unchanged (not used for this count)
9. No `created_by` / `mint_ip` attribution columns

## Evidence (path:lines)

| Piece | Where |
|---|---|
| Gate | `agent_coord/server/admin/guard.py` `require_invite_seat_mint` (reuse) |
| Count SQL | `agent_coord/server/admin/seats.py` `seat_count` |
| HTTP | `agent_coord/server/admin/invites.py` `action in (seat_count, count_seats, invite_count)` |
| Docs | `docs/requirements/invite.md` §5 |
| Tests | `tests/install/test_invite_seat.py` |

## Out of scope

- `agent_coord/web/wall_ui/**`
- Door invite flows beyond counting
- Per-owner / per-IP attribution
- Live SQL apply (no schema change)
- Push / pack / PyPI

## Self-test

```
pytest tests/install/test_invite_seat.py -q
```

## Ready for Validator when

- Tip SHA committed locally
- pytest green for `test_invite_seat.py`
- Exact wall-ui request/response documented below

## Wall-ui contract

Request:
```json
POST /api/admin/invites
{ "action": "seat_count", "owner": "<badge desk>", "token": "<human badge when required>" }
```

Response:
```json
{ "ok": true, "invites": 29, "joined": 4 }
```

Host display map: `joined (joined) / invites (invited)` -> e.g. `4 (joined)/ 29 (invited)`.
