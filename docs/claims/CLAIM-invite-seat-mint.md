# Claim - invite-seat mint (one agent URL)

Status: **RC Ready** on `claim/floor-v1-parts`. Local commit only. Not pushed. Not PyPI.

## Intent

Humans (and Admin agents) mint **one agent invite URL per call** = one seat.
Wall-ui welcome glass will consume the URL later (out of scope).

## Acceptance (Host locked)

1. One mint = one seat; mint again per agent.
2. trust=high: human badge OR ROLE_Admin. trust=limited: ROLE_Admin only.
3. URL: `https://<wall>/welcome?desk=<DESK_slug>&seat=<plaintext_once>`
4. Response: `invite_url`, `desk`, `seat` (plaintext once); book stores `token_hash` only.
5. Not wall_ui. No door pending `--enable` for seats (status `ready`).
6. Extend `POST /api/admin/invites` `action=mint_seat` + verb `invite-seat` / `mill invite --seat DESK`. Door mint/list/enable/revoke unchanged.

## Evidence (path:lines)

| Piece | Where |
|---|---|
| Gate | `agent_coord/server/admin/guard.py` `require_invite_seat_mint` |
| Mint + URL | `agent_coord/server/admin/seats.py` `mint_seat` / `invite_url_for` |
| HTTP | `agent_coord/server/admin/invites.py` `action in (mint_seat, seat)` |
| Verb | `agent_coord/server/api/mill/rpc.py` `_h_invite_seat` + HANDLERS `invite-seat` |
| WALL set | `agent_coord/client/outbound/__init__.py` |
| CLI | `agent_coord/__main__.py` `--seat DESK`; prints `invite_url` |
| Docs | `docs/requirements/invite.md` §5; `admin.md` Always-Admin vs trust-gated |
| Tests | `tests/install/test_invite_seat.py` |

## Out of scope

- `agent_coord/web/wall_ui/**` welcome glass consume
- Door key pending/enable lifecycle changes
- Push / pack / PyPI

## Self-test

```
pytest tests/install/test_invite_seat.py -q
```

## Ready for Validator when

- Tip SHA committed locally with message matching mint one-seat intent
- pytest green for `test_invite_seat.py`
- Existing door invite tests still pass (`test_invite_admin.py`)
