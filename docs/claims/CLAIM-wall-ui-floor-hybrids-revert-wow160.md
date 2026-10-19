# Claim - Wall UI FLOOR hybrids revert to /api/floor (wow160)

Status: **local WIP** on `claim/floor-v1-parts`. Committed locally only. Not pushed. Not pack/PyPI. No Playwright.

Parent tip: current branch tip past wow159 (`76a4176`). Supersedes happy-path of `docs/claims/CLAIM-wall-ui-v1-floor-hybrids-wow159.md` (kept as history).
Contract base: `docs/claims/WALL-CONTRACT-floor-v1-parts.md` + Builder `_V1_PARTS`.
Measure + Builder lock: FLOOR Map/Timeline hybrid parallel v1 fan-out off until joined Claim.

## Lock

Revert FLOOR multi-part happy paths (`agents,mail` / `agents,events` / `agents,timeline`) back onto `/api/floor` (pre-wow159 aggregator). Keep wow158 single-pane v1 (SESSION agents/holds/watchers/events, SCORE, GLOSSARY, MAIL rooms/mailbox/tree-mail, TODO todos/tree-todo) and sticky V1-down `/api/floor` fallbacks. Human-readonly GET-only. No invented Loop-2 / joined endpoints. No Builder SoR in Wall commits. No push / pack / PyPI / Playwright.

## Routes (project scope, v1 up)

| Wall surface | parts= | happy path | notes |
|--------------|--------|------------|-------|
| FLOOR Map | `agents,mail` | `/api/floor` | reverted off parallel v1 |
| FLOOR Timeline/LAN | `agents,events` | `/api/floor` | reverted off parallel v1 |
| FLOOR Timeline/project | `agents,timeline` | `/api/floor` | unchanged (never had v1) |
| SCORE / SESSION / glossary / MAIL / TODO | unchanged | prior wow157/158 v1 | kept |

Sticky down -> `wallFetchFloorParts` / `/api/floor?parts=` as before.

## What landed

1. **`boot.js`** - remove FLOOR hybrid `wallV1Routes` fan-out; restore multi-on-floor comments; early-absorb back to session/score/glossary only; header wow160.
2. **`board.html`** - `boot.js?v=wow160`.
3. **Tests** - hybrid asserts `/api/floor` again; cache-bust wow160.
4. **This claim**; wow159 claim left as superseded history.

## Evidence (path:lines)

- Header: `agent_coord/web/wall_ui/default/boot.js` wow160 FLOOR hybrids back on `/api/floor`
- Routes: `wallV1Routes` has no `parts === "agents,mail"` / `agents,events` branches
- Early absorb: session/score/glossary only (no floor+mailbox)
- Cache-bust: `agent_coord/web/wall_ui/default/board.html` `boot.js?v=wow160`
- Tests: `tests/wall/test_wall_ui_floor_v1_consume.py`

## Glance (host / Operator)

1. Recycle **mill-wall** so checkout serves this tip.
2. Hard-refresh Wall (`boot.js?v=wow160`).
3. FLOOR Map Network: `/api/floor?parts=agents,mail` (not parallel v1) when healthy.
4. FLOOR Timeline/LAN: `/api/floor?parts=agents,events`.
5. FLOOR Timeline project: `/api/floor?parts=agents,timeline`.
6. SESSION/SCORE/glossary/MAIL/TODO single-pane v1 unchanged; sticky-down still falls back to `/api/floor`.

## Out of scope

- Push / pack / PyPI / Playwright / mill-wall recycle (host)
- Inventing joined `/api/v1/*` hybrid endpoints
- Builder `floor.py` / middleware edits in Wall commits
- Changing mail.js / shell.css cache tags this ship

## Supersedes

`CLAIM-wall-ui-v1-floor-hybrids-wow159.md` happy-path (parallel v1 hybrids). That claim remains as history of the measure that Builder+host locked off pending joined Claim.
