# Claim - Wall UI glass consume /api/v1/map + /api/v1/timeline (wow163)

Status: **local WIP** on `claim/floor-v1-parts`. Committed locally only. Not pushed. Not pack/PyPI. No Playwright.

Parent tip: Builder joined isolates (`753337e` `CLAIM-v1-map-timeline.md`) on wow162 glass.
Supersedes happy-path of wow160 floor-only hybrids (`CLAIM-wall-ui-floor-hybrids-revert-wow160.md`).
Contract: `docs/claims/CLAIM-v1-map-timeline.md` + floor merge keys.

## Roles only

No personal identifiers in commits, Claims, or docs - roles only (host, desk, human, agent, ROLE_Admin, PROJ_Office).

## Lock

Wire FLOOR Map / Timeline hybrids onto Builder **joined** v1 isolates (one RTT each). Do **not** reintroduce Promise.all of agents+mailbox (wow159 fan-out). Sticky 404/down stays `/api/floor?parts=`. Human-readonly GET-only. No Builder SoR in Wall commits. No push / pack / PyPI / Playwright.

## Routes (project scope, v1 up)

| Wall surface | parts= | happy path | sticky down |
|--------------|--------|------------|-------------|
| FLOOR Map | `agents,mail` | `GET /api/v1/map?project=` | `/api/floor?parts=agents,mail` |
| FLOOR Timeline LAN | `agents,events` | `GET /api/v1/timeline?project=` | `/api/floor?parts=agents,events` |
| FLOOR Timeline project | `agents,timeline` | `GET /api/v1/timeline?project=&parts=agents,timeline` | `/api/floor?parts=agents,timeline` |

Also: `?fp=` empty-on-match (composite parts), `?limit=50` first page, `?timings=1` when wall_perf (existing perf.js wrap). Response keys match floor merge (`agents` + `mailbox`|`events`|`timeline`, `fp`, `next`, `parts`, optional `desk_unread` / `timings`).

## What landed

1. **`boot.js`** - `wallV1Routes` FLOOR hybrids -> single joined route (`map` / `timeline` + `fpParts` / `queryParts`); `wallMergeV1Isolates` pass-through for joined payload; `wallFetchFloorV1` limit+fp+parts for map/timeline; header wow163.
2. **`board.html`** - `boot.js?v=wow163`.
3. **Tests** - hybrid joined asserts; cache-bust wow163 across wall tests (score.js stays wow162).
4. **This claim**.

## Evidence (path:lines)

- Header: `agent_coord/web/wall_ui/default/boot.js` wow163 joined map/timeline note
- Routes: `wallV1Routes` `parts === "agents,mail"|"agents,events"|"agents,timeline"`
- Merge: `wallMergeV1Isolates` `kind === "map" || kind === "timeline"`
- Fetch: `wallFetchFloorV1` `fpParts` / `queryParts` / pageKinds map+timeline
- Cache-bust: `board.html` `boot.js?v=wow163`
- Tests: `tests/wall/test_wall_ui_floor_v1_consume.py`

## Glance (host / Operator)

1. Recycle **mill-wall** so checkout serves this tip (needed if still on 0.5.8 wheel without map/timeline).
2. Hard-refresh Wall (`boot.js?v=wow163`).
3. FLOOR Map Network: `/api/v1/map?project=...` (one request; not agents+mailbox).
4. FLOOR Timeline/LAN: `/api/v1/timeline?project=...`.
5. FLOOR Timeline project: `/api/v1/timeline?project=...&parts=agents,timeline`.
6. Sticky-down / 404: falls back to `/api/floor?parts=...` as before.
7. `?wall_perf=1`: map/timeline GETs get `timings=1` via existing perf.js.

## Out of scope

- Push / pack / PyPI / Playwright / mill-wall recycle (host)
- Builder `floor.py` / middleware edits in Wall commits
- Re-fan-out Promise.all agents+mailbox
- Changing mail.js / score.js / shell.css cache tags this ship
- OIDC / admin / build-tui WIP

## Supersedes

`CLAIM-wall-ui-floor-hybrids-revert-wow160.md` happy-path (hybrids on `/api/floor`). Sticky-down path unchanged.
