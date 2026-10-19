# Claim - Wall UI consume frozen floor v1 parts

Status: **local WIP** on `claim/loop-3-wall-mail-rooms`. Committed locally only. Not pushed. Not PyPI.

Parent Builder SoR: `claim/floor-v1-parts` @ `b6df10da0fc5cd72532da7f78ca807cea7b9db89` (clean of SoR WIP).  
Contract: `docs/claims/WALL-CONTRACT-floor-v1-parts.md` (also evidence `~/.mill\evidence\builder-floor-parts-split-20260926\`).  
Samples: same evidence folder `sample-*.json`.  
Glass base: Loop-3 tip ~`30aad5c` / `boot.js?v=wow135` human-readonly ON.

## Lock

Wire wall_ui to consume frozen `/api/v1/{rooms,mailbox,tree-mail,tree-todo,todos}?project=<slug>` isolates. **Do not invent API** - field keys and path names from Builder WALL-CONTRACT only. Keep `/api/floor?parts=&fp=` fallback. Progressive trees PARKED. Human-readonly stays ON (GET-only). No Builder server SoR in Wall commits. No push / Playwright / pack / PyPI.

## Routes consumed (project scope only)

| Wall surface | v1 GETs | Floor-shaped keys after merge |
|--------------|---------|-------------------------------|
| MAIL Rooms | `/api/v1/rooms` + `/api/v1/mailbox` + `/api/v1/tree-mail` | `trees` (prefer tree-mail over lean rooms), `mailbox`, `desk_unread`, `fp.mail` |
| MAIL nest/list (list/graph) | `/api/v1/mailbox` | `mailbox`, `desk_unread`, `fp.mail` |
| TODO Nest/List/Board | `/api/v1/todos` + `/api/v1/tree-todo` | `needs`, `issues`, `fp.todos`, `trees` |
| Other tabs (session/score/floor/...) | still `/api/floor?parts=<wallParts()>&fp=` | unchanged |

lan/role scope: v1 first-ship is project-only -> Wall keeps aggregator for lan picks.

## Fallback

1. Try v1 isolates when `wallV1Routes(scope)` returns routes.
2. Any isolate **404** / non-JSON / !ok / fetch throw -> set sticky `_wallFloorV1Down` and **that tick** uses existing `GET /api/floor?<scope>&parts=<wallParts()>&fp=...` (+ empty-on-match fp consume).
3. While sticky down, all subsequent ticks skip v1 (host must run Builder checkout + host restart wall; hard-refresh loads `boot.js?v=wow136`).

## What landed

1. **`boot.js`** - `wallV1Routes` / `wallMergeV1Isolates` / `wallFetchFloorV1` / `_wallFloorV1Down`; `_tickBody` tries v1 then floor fallback.
2. **`board.html`** - `boot.js?v=wow136`.
3. **Tests** - `tests/wall/test_wall_ui_floor_v1_consume.py`; floor-fp cache-bust assert bumped to wow136.
4. **This claim** - `docs/claims/CLAIM-wall-ui-floor-v1-consume.md`.

## Behavior matrix

| Case | Client | Server | Glass |
|------|--------|--------|-------|
| MAIL Rooms + v1 live | parallel rooms+mailbox+tree-mail | mill-stamped isolates | merge -> absorbFloorSlice; tree-mail wins `trees` |
| MAIL list + v1 live | mailbox only | mailbox isolate | mail paint / fp.mail remember |
| TODO + v1 live | todos+tree-todo | isolates | jobs/nest paint |
| v1 404 / down | sticky flag | n/a | `/api/floor` + `parts=` + `fp=` (prior Loop-3 path) |
| session/score/... | no v1 routes | floor aggregator | unchanged |

## Evidence (path:lines)

- Helpers: `agent_coord/web/wall_ui/default/boot.js` `wallV1Routes` / `wallMergeV1Isolates` / `wallFetchFloorV1` (~998+)
- Poll: `_tickBody` usedV1 + floor fallback (~6285+)
- Cache-bust: `agent_coord/web/wall_ui/default/board.html` `boot.js?v=wow136`
- Tests: `tests/wall/test_wall_ui_floor_v1_consume.py`

## Glance (host)

1. Host runs `claim/floor-v1-parts` checkout; **restart mill-wall**.
2. Hard-refresh Wall (`boot.js?v=wow136`).
3. MAIL -> Rooms: Network shows `/api/v1/rooms`, `/api/v1/mailbox`, `/api/v1/tree-mail` (or `/api/floor` if v1 sticky-down).
4. TODO Nest/List/Board: `/api/v1/todos` + `/api/v1/tree-todo`.
5. Human-readonly still ON (no compose write chrome).

## Out of scope

- Progressive trees / cursor protocol
- lan/role on v1
- agents/scores/holds/office v1 follow routes
- Committing Builder `floor.py` / middleware SoR into Wall commits
- Push / pack / PyPI / Playwright
- Service restart (host)

## Hold

`mill hold` not required for glass-only edit under `agent_coord/web/wall_ui` + claims/tests.
