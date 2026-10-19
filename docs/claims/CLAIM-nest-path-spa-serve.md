# CLAIM nest-path-spa-serve

Status: **local WIP / Ready for Validator** on `claim/floor-v1-parts`. Local commit only. Not pushed. Not pack/PyPI.

Parent: `docs/claims/LOOP2-nest-path-spa-serve.md` (Wall glass wow175 / wow177 handoff). Hub must serve Nest board for deep-link path families so hard refresh / cold open does not 404.

## Lock

Serve the same Nest board HTML for:

| Path | Serve board |
|------|-------------|
| `/`, `/board`, `/index.html`, `/welcome` | exact (existing) |
| `/projects`, `/projects/*` | prefix (boundary-safe) |
| `/stations`, `/stations/*` | prefix (IPv4 slug ok: `/stations/192.0.2.10`) |
| `/roles`, `/roles/*` | prefix |

Shared helper `_is_nest_board_path` used at closed-door login redirect, invite-query strip, and board serve so Nest deep links get consistent invite/login/board behavior.

Do **not** break `/api/*`, static files, or mill routes. Prefix match: `path == prefix` or `path.startswith(prefix + "/")` (so `/projectsfoo` is not board).

## Files

- `agent_coord/server/middleware.py` - `_is_nest_board_path` + three call sites
- `tests/server/test_asgi.py` - Nest SPA serve + api-only block
- this claim
- Loop-2 note kept as handoff context (not rewritten)

## Claims with path:lines (Builder)

| Claim | Path |
|-------|------|
| Shared Nest board-path helper | agent_coord/server/middleware.py:323-340 |
| Closed-door login redirect uses helper | agent_coord/server/middleware.py:870 |
| Invite strip uses helper | agent_coord/server/middleware.py:889 |
| Board serve uses helper | agent_coord/server/middleware.py:894 |
| Tests Nest deep links 200 board | tests/server/test_asgi.py:78-108 |
| Tests api-only still blocks board | tests/server/test_asgi.py:111-120 |

## Acceptance (glance)

```text
GET /projects/the-mill          -> 200 text/html board (THE MILL)
GET /stations/192.0.2.10      -> 200 text/html board
GET /roles/Admin                -> 200 text/html board
GET /projectsfoo                -> 404 (not board)
GET /api/howto                  -> 200 application/json (not board)
```

After Hub recycle: wall-ui may re-enable `NEST_PATH_WRITE` (wow177 guard).

## Out of scope

- Push / pack / PyPI
- `wall_ui/**` edits / NEST_PATH_WRITE flip (Wall)
- Floor API `lan=` / `project=` contracts
- wall-ui cosmetic error-page / OIDC callback WIP (neighbor dirt; not this Claim)
