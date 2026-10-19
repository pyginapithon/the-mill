# Claim - Wall UI SESSION Now agents via GET /api/v1/agents (wow157)

Status: **local WIP** on `claim/floor-v1-parts`. Committed locally only. Not pushed. Not pack/PyPI. No Playwright.

Parent Builder SoR: `d6f317d` (`v1 agents: isolate from floor aggregator`).
Contract base: `docs/claims/WALL-CONTRACT-floor-v1-parts.md` + Builder middleware `_V1_PARTS` agents / `floor.py` `v1_agents`.
Prior glass: wow155/wow156 v1 consume (mail/todos) on same branch.

## Lock

Wire wall_ui to consume Builder `GET /api/v1/agents?project=...` (+ optional `fp=agents:hex`, `limit`, `cursor`) for **SESSION Now** when `wallParts()` is exactly `agents`. Keep sticky `/api/floor` fallback. Multi-part floor panes (`agents,mail` / `agents,events` / `agents,timeline`) stay on aggregator until later isolates. Human-readonly GET-only. No Builder SoR in Wall commits. No push / pack / PyPI / Playwright.

## Routes (project scope, v1 up)

| Wall surface | v1 GETs | Notes |
|--------------|---------|-------|
| SESSION Now | `/api/v1/agents` | `wallParts()=="agents"`; session mode now or missing |
| FLOOR agents-only | `/api/v1/agents` | none today (multi stays floor) |
| MAIL / TODO | unchanged | rooms/mailbox/tree-*/todos |
| score/glossary/leases/watch/history | still `/api/floor` | wallV1Routes null |

Response merge (floor-shaped): `addPart("agents")`, `out.agents`, `out.next_agents` from `json.next`. First page `?limit=50` + `floorFpQuery(scope,"agents")`. Scroll next: `/api/v1/agents?...&limit=50&cursor=` when v1 up; else `/api/floor?...&parts=agents&limit=50&cursor=`.

## What landed

1. **`boot.js`** - wallV1Routes agents; wallMergeV1Isolates agents; fetchOne limit+fp+remember; list-next v1/floor; optional session early absorb.
2. **`board.html`** - `boot.js?v=wow157` (mail.js stays wow156; shell stays wow155).
3. **Tests** - `tests/wall/test_wall_ui_floor_v1_consume.py` + boot cache-bust wow157 across wall tests that hardcoded wow155 for boot.js.
4. **This claim**.

## Evidence (path:lines)

- Routes: `agent_coord/web/wall_ui/default/boot.js:1519-1534` (`wallV1Routes` agents)
- Merge: `boot.js:1577-1580` (`addPart("agents")`, `out.agents`, `out.next_agents`)
- Fetch: `boot.js:1598-1614` (limit=50, `floorFpQuery(scope.key, "agents")`, `wallRememberListNext`)
- Early absorb: `boot.js:7193+` (`_tickBody` onRow session agents)
- List-next: `boot.js:7809-7815` (`/api/v1/agents?` / floor sticky)
- Cache-bust: `agent_coord/web/wall_ui/default/board.html:692` `boot.js?v=wow157`
- Tests: `tests/wall/test_wall_ui_floor_v1_consume.py`

## Glance (host)

1. Recycle **mill-wall** so it serves this checkout (Builder tip includes `d6f317d`).
2. Hard-refresh Wall (`boot.js?v=wow157`).
3. SESSION -> Now: Network shows `GET /api/v1/agents?project=...` (or `/api/floor` if sticky-down).
4. Validator remasure after recycle.

## Out of scope

- Push / pack / PyPI / Playwright / mill-wall recycle (host)
- scores/holds/watchers/events/timeline v1 isolates
- Builder `floor.py` / middleware edits in Wall commits
- Changing mail.js / shell.css cache tags this ship