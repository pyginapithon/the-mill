# Claim - v1 tree-mail/todo ?window= (#58 nest-mail-filter-windows)

Status: **RC Ready** on claim/floor-v1-parts. Local commit only. Not pushed. Not pack/PyPI.
Parent: WALL-CONTRACT-v1-trees-progressive.md / #55 progressive trees. Mill card **#58**.
Contract: docs/claims/WALL-CONTRACT-v1-trees-window.md (**Host GO / implement**).

## Lock (Host GO 2026-09-27 PT)

| Item | Lock |
|------|------|
| Routes | GET /api/v1/tree-mail + GET /api/v1/tree-todo only |
| Query | ?window=1d\|1w\|30d ; omit/empty = **All** (no time filter) |
| Semantics | Keep forests whose last TREE activity (MAX activity.updated under forest, all node types) is within window |
| Invalid window | HTTP **400** clear error |
| Response | trees + next + mill (unchanged) |
| Progressive | limit/cursor/depth/parent_id/has_children unchanged |
| Floor parts=trees | **sticky follow** -- not this shot |

## Files

- agent_coord/server/records/floor.py - parse_tree_window, filter_trees_by_window, v1_tree_* wire
- agent_coord/server/records/tree.py - forest_last_activity
- agent_coord/server/middleware.py - pass window; 400 on invalid
- tests/server/test_v1_trees_window.py (6)
- docs/claims/WALL-CONTRACT-v1-trees-window.md + this claim

## Claims with path:lines (Builder)

| Claim | Path |
|-------|------|
| Window tokens + parse (omit=All; invalid raises) | agent_coord/server/records/floor.py:258-290 |
| Forest filter by last activity | agent_coord/server/records/floor.py:293-310 |
| v1 tree-mail window filter then progressive | agent_coord/server/records/floor.py:1655-1683 |
| v1 tree-todo window filter then progressive | agent_coord/server/records/floor.py:1686-1714 |
| MAX(activity.updated) per TREE name | agent_coord/server/records/tree.py:180-211 |
| Middleware pass + 400 | agent_coord/server/middleware.py:1347-1380 |
| Tests | tests/server/test_v1_trees_window.py (6) |
| activity.updated SoR | agent_coord/server/sql/tables.sql:35-52 |

## Validator

1. omit window -> same progressive All stream
2. window=1d drops forests with last TREE activity older than 1d
3. window=2d (or 24h) -> 400
4. window=1w + limit/cursor/depth still pages kept forests

## Follow

1. Measure on live Wall host
2. Floor parts=trees window sticky if GO
3. wall-ui All|1d|1w|30d chips

## Out of scope

Push, mill-wall recycle, SP apply, floor parts=trees window, wall_ui glass, new window tokens.

## Roles only

Builder / wall-ui / Operator / Validator / Host -- no personal names or home paths.

## Mill todos

| id | need_id | Status |
|----|---------|--------|
| 58 | nest-mail-filter-windows | **RC Ready** (v1 tree-mail + tree-todo this shot) |
