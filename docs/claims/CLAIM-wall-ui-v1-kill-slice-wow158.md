# Claim - Wall UI floor kill-slice glass consume v1 scores/holds/watchers/events/names (wow158)

Status: **local WIP** on `claim/floor-v1-parts`. Committed locally only. Not pushed. Not pack/PyPI. No Playwright.

Parent tip: `f8bbcf5` (`v1 names: isolate from floor aggregator`).
Contract base: `docs/claims/WALL-CONTRACT-floor-v1-parts.md` + Builder middleware `_V1_PARTS` + `floor.py` `v1_*`.
Prior glass: wow157 SESSION Now agents + wow155/wow156 mail/todos on same branch.

## Lock

Batch-wire remaining single-part floor tabs off `/api/floor` onto frozen v1 isolates. Prefer **single-part tabs only** to v1; multi (`agents,mail` / `agents,events` / `agents,timeline`) stay on floor aggregator until hybrid later. Sticky `/api/floor` fallback on v1 404. Human-readonly GET-only. No Builder SoR in Wall commits. No push / pack / PyPI / Playwright.

## Routes (project scope, v1 up)

| Wall surface | v1 GET | kind | body keys |
|--------------|--------|------|-----------|
| SCORE tab | `/api/v1/scores` | scores | `kpis`, `next`, `fp.scores` |
| SESSION leases | `/api/v1/holds` | holds | `locks`, `next`, `fp.holds` |
| SESSION watch | `/api/v1/watchers` | watchers | `watchers`, `next`, `fp.watchers` |
| SESSION history | `/api/v1/events` | events | `events`, `next`, `fp.events` |
| glossary tab | `/api/v1/names` | names | `catalog`, `next`, `fp.names` |
| SESSION Now | `/api/v1/agents` | agents | keep (wow157) |
| MAIL / TODO | unchanged | | rooms/mailbox/tree-*/todos |
| FLOOR map `agents,mail` | `/api/floor` | multi | stay floor |
| FLOOR timeline `agents,events` | `/api/floor` | multi | stay floor |

Merge (floor-shaped): `addPart` + body field + `next_<kind>` from isolate `json.next`. First page `?limit=50` + `floorFpQuery(scope, part)`. Scroll next: `/api/v1/<part>?...&limit=50&cursor=` when v1 up; else `/api/floor?...&parts=<part>&limit=50&cursor=`.

## What landed

1. **`boot.js`** - wallV1Routes score/leases/watch/history/glossary; wallMergeV1Isolates each kind + next_*; fetchOne pageKinds+fpKinds; wallFetchListNextPage v1 URLs; optional early absorb; header kill-slice comment.
2. **`board.html`** - `boot.js?v=wow158`.
3. **Tests** - `tests/wall/test_wall_ui_floor_v1_consume.py` (all routes present; no invent beyond set) + boot cache-bust wow158 across wall tests.
4. **This claim**.

## Evidence (path:lines)

- Header: `agent_coord/web/wall_ui/default/boot.js:1489-1491` (kill-slice glass consume complete pending recycle)
- Routes: `boot.js:1520-1545` (score/glossary/holds/watchers/events + agents keep)
- Merge: `boot.js:1588-1612` (`kpis`/`locks`/`watchers`/`events`/`catalog` + `next_*`)
- Fetch: `boot.js:1630-1656` (pageKinds + fpKinds + limit=50 + remember)
- Early absorb: `boot.js:7233+` (`_tickBody` onRow single-part)
- List-next: `boot.js:7857-7875` (v1 paths / floor sticky)
- Cache-bust: `agent_coord/web/wall_ui/default/board.html:692` `boot.js?v=wow158`
- Tests: `tests/wall/test_wall_ui_floor_v1_consume.py`

## Glance (host)

1. Operator recycle **mill-wall** so it serves this checkout (Builder tip includes `f8bbcf5` + prior v1 isolates).
2. Hard-refresh Wall (`boot.js?v=wow158`).
3. Network on each tab: SCORE -> `/api/v1/scores`; SESSION leases/watch/history -> holds/watchers/events; glossary -> names; SESSION Now -> agents (keep). FLOOR map/timeline stay `/api/floor`. Sticky-down shows `/api/floor?parts=...`.
4. Validator remasure after recycle.

## Out of scope

- Push / pack / PyPI / Playwright / mill-wall recycle (host)
- Hybrid multi-part v1 (agents+mail / agents+events)
- Builder `floor.py` / middleware edits in Wall commits
- Changing mail.js / shell.css cache tags this ship
