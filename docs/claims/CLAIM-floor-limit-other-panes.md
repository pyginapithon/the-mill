# Claim - Builder Loop-2 floor parts + activity limit+cursor (#49?54)

Status: **local WIP** on `claim/floor-v1-parts`. Committed locally only. Not pushed. No mill-wall recycle (Operator).

Parent: v1 mailbox/todos paging (`CLAIM-v1-limit-cursor.md`) + lean list truncate.
Evidence: `~/.mill/evidence/builder-v1-limit-other-panes-20260926/`
Contract: `docs/claims/WALL-CONTRACT-v1-limit-cursor.md` (universal shape + matrix updated).
Widen: host ? page limit applies to ALL dense content panes; trees PARK progressive (#55).


## Major fix (2026-09-26 PT) - events next after board_view TTL

Validator Major @ 600fdf1: `/api/floor?parts=events` could return `next` (e.g. `todo:50`)
while `events=[]` because `apply_floor_list_page` ran **before** `snapshot`->`board_view`
TTL dropped aged events.

**Fix:** `floor` / `floor_scope` return full lists (limit/cursor kwargs kept for signature);
`middleware` `/api/floor` runs `snap(...)` then `apply_floor_list_page` so `next` matches
post-TTL / fixture-filtered lists. Same order covers sibling dense parts (fixture drops).

| Item | Path |
|------|------|
| Page after snap | `agent_coord/server/middleware.py` (~1390-1435) |
| No pre-snap page | `agent_coord/server/records/floor.py` (`floor` / `floor_scope` return) |
| Contract note | `apply_floor_list_page` docstring |
| Regression | `tests/server/test_floor_limit_cursor.py::test_events_page_after_board_view_ttl` |
| Evidence | `~/.mill/evidence/builder-floor-events-next-fix-20260926/` |

Trees **PARK** #55 - untouched. cloud-mill #40 / #49-54 note only. No mill-wall recycle.

## Lock (shipped N=50)

| Item | Lock |
|------|------|
| Routes | `/api/floor?parts=mail\|todos\|agents\|scores\|holds\|watchers\|events` + `/api/activity` |
| Query | `?limit=` default **50** (clamp 1..500); `?cursor=` opaque last-row key |
| Response | `next` cursor or `null`; trees **untouched** |
| Paging | Python via `apply_floor_list_page` / `page_activity_rows` after full build |
| Primary cursor | first of mail?todos?agents?scores?holds?watchers?events in `parts=` |
| Prefer | wall prefers `/api/v1/mailbox` + `/api/v1/todos` when isolating those panes; floor parts mirror same shape |
| Trees | **PARK** #55 ? progressive depth/page N=50 later |
| Validator | unit tests `test_floor_limit_cursor.py`; curl smoke on this machine |

## Files

- `agent_coord/server/records/floor.py` ? `page_by_cursor` key/get_key; `apply_floor_list_page`; `page_activity_rows`; floor/floor_scope `limit`/`cursor`; row `id` on agents/locks/kpis
- `agent_coord/server/middleware.py` ? pass limit/cursor into floor + activity; cache key includes lim/cur
- `tests/server/test_floor_limit_cursor.py`
- `docs/claims/WALL-CONTRACT-v1-limit-cursor.md` + this claim
- Evidence samples + measure notes

## Claims with path:lines (Builder)

| Claim | Path |
|-------|------|
| Helpers page + apply | `agent_coord/server/records/floor.py` (`page_by_cursor`, `apply_floor_list_page`, `page_activity_rows`) |
| Floor + scope (full lists) | `agent_coord/server/records/floor.py` (`floor`, `floor_scope`; page deferred) |
| Page after board_view | `agent_coord/server/middleware.py` (`snap` then `apply_floor_list_page`) |
| Middleware wire | `agent_coord/server/middleware.py` (`/api/floor`, `/api/activity`) |
| Tests | `tests/server/test_floor_limit_cursor.py` |

## Follow

1. Trees progressive depth/page N=50 (**PARK** #55 ? explicit)
2. `/api/office-glance` only if fat after measure
3. wall-ui infinite scroll on floor parts / activity (after Operator recycle)

## Out of scope

Push, mill-wall recycle, SP apply, progressive trees implement, wall_ui glass edits.

## Roles only

Builder / wall-ui / Operator / Validator ? no personal names or home paths.

## Mill todos (this shot)

| id | need_id | Status |
|----|---------|--------|
| 49 | v1-page-floor-mail | **done** (this shot) |
| 50 | v1-page-floor-todos | **done** |
| 51 | v1-page-floor-agents | **done** |
| 52 | v1-page-floor-scores | **done** |
| 53 | v1-page-floor-session-parts | **done** |
| 54 | v1-page-activity | **done** |
| 55 | v1-page-trees-progressive | **PARK** |
| 40 | wall-ui-perf-rebuild (cloud-mill parent) | note only ? GitHub hang blocked (MCP needsAuth) |
