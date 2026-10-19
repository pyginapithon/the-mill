# Claim - Wall UI MAIL Rooms two-phase left-rail paint + cold-SQL stagger

Status: **local WIP** on `claim/floor-v1-parts`. Committed locally only. Not pushed.

Parent: wall-ui consume floor v1 parts + wall_perf wow137 (`8d9ddf9`) + two-phase paint wow138 + strip spinners wow142.

## Lock

Phase-1 paint the MAIL Rooms **left rail** as soon as `tree-mail` (or `rooms`) lands. Do **not** gate first rail paint on mailbox (~201KB / ~460ms). Phase-2 mailbox re-sorts (`mailRoomLatestAt`), badges, cast size, search haystack, nest/body.

**Loop-3 cold-SQL stagger (wow143):** do **not** `Promise.all` rooms + mailbox + tree-mail. Fetch **phase A** (`rooms` + `tree-mail`) first (parallel OK); start **phase B** (`mailbox`) only after A settles (early rail already painted via `onRow`). Keep sticky `/api/floor` fallback. Humans readonly unchanged. `wall_perf` stays opt-in. Keep v1 routes; no Loop-2 SoR change. No push / Playwright / pack / PyPI / service restart.

## What landed

1. **`boot.js`** (`wow138`) - `wallFetchFloorV1(..., onRow)` streams each isolate; `_tickBody` paints rail from tree-mail/rooms; mailbox enriches.
2. **`boot.js`** (`wow143`) - MAIL Rooms fetch stagger inside `wallFetchFloorV1`: phase A rooms+tree-mail, phase B mailbox after A. Other route sets stay parallel.
3. **`paintMailRooms(d, { railOnly })`** - first rail can skip nest; rail sig adds `mb0`/`mb1` so Phase 2 rebuilds once.
4. **board.html / static board.html** - `boot.js?v=wow143` (shell.css stays wow142).
5. **Tests** - `tests/wall/test_wall_ui_mail_rooms_two_phase.py` (+ stagger); cache-bust asserts bumped to wow143.
6. **This claim**.

## Rooms trio (kept)

`/api/v1/rooms` stays in the MAIL Rooms trio. Merge still prefers tree-mail over lean rooms. **Not dropping rooms**: tree-mail is typed mail forests; rooms is the lean mail-root isolate. Not proven tree-mail always supersets rooms (empty/slow/shape). Rooms remains a Phase-1 label source if it lands first. Stagger only changes **fetch order**, not which routes are requested.

## Behavior

| Phase | Trigger | Glass |
|-------|---------|-------|
| A fetch | rooms + tree-mail parallel | Network: mailbox not started yet |
| 1 paint | tree-mail or rooms isolate lands (`onRow`) | left rail titles (tree order / best-effort; no mailbox sort) |
| B fetch | after phase A settles | mailbox GET starts |
| 2 paint | mailbox isolate lands (after trees exist) | re-sort by `mailRoomLatestAt`, unread badges, cast N, search haystack, nest/body |
| mailbox-only (list/graph) | single route | unchanged parallel/single fetch |
| todos + tree-todo | parallel | unchanged |
| v1 404 / down | sticky `_wallFloorV1Down` | same-tick `GET /api/floor?parts=&fp=` (phase A down skips mailbox) |
| list/graph / other tabs | unchanged | mailbox-only v1 or floor aggregator |

## Evidence (path:lines)

`agent_coord/web/wall_ui/default/boot.js`:

- Floor v1 + stagger comments: `1146:1157`
- `wallV1Routes` rooms trio kept: `1160:1183`
- `wallMergeV1Isolates`: `1185:1230`
- `wallFetchFloorV1` fetchOne + phaseA/phaseB stagger: `1231:1280`
- `wallMailRoomsWantEarlyRail` / `wallPaintMailRoomsEarly`: `1281:1307`
- `_tickBody` `onRow` -> early rail (not gated on mailbox): ~`6768:6818`
- sticky `/api/floor` fallback: ~`6831`
- Cache-bust: `agent_coord/web/wall_ui/default/board.html` `boot.js?v=wow143`
- Tests: `tests/wall/test_wall_ui_mail_rooms_two_phase.py`, `tests/wall/test_wall_ui_floor_v1_consume.py`

## Glance (host)

1. Recycle mill-wall so it serves this checkout (or confirm `MILL_WALL_SRC=git` already points here).
2. Hard-refresh Wall (`boot.js?v=wow143`).
3. MAIL -> Rooms. Network: `/api/v1/rooms` + `/api/v1/tree-mail` start together; `/api/v1/mailbox` starts **after** those settle (not in the same Promise.all wave).
4. Left rail titles appear from tree-mail/rooms **before** mailbox finishes.
5. After mailbox: rail re-sorts / badges / cast; nest fills.
6. Optional: `?wall_perf=1` then `wallPerfDump()` - `first_mail_rooms_rail` (phase 1) then `first_mail_rooms_rail_mb` (phase 2). Off path stays zero-cost.

## Out of scope

- Dropping `/api/v1/rooms` from the trio
- Lean meta-only mailbox (needs Builder `parts=`)
- Progressive trees / lan-role v1
- Loop-2 SoR / floor.py changes
- Push / pack / PyPI / Playwright / mill-wall restart from this agent
