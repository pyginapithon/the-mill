# Claim - v1 progressive trees (depth-cap + limit/cursor) (#55)

Status: **RC Ready** on claim/floor-v1-parts. Local commit only. Not pushed. Not pack/PyPI.
Parent PARK: WALL-CONTRACT-v1-limit-cursor.md trees PARK; mill todo **#55**.
Contract: docs/claims/WALL-CONTRACT-v1-trees-progressive.md (**Host GO / implement**).
Prior full slice: CLAIM-floor-v1-parts.md / WALL-CONTRACT-floor-v1-parts.md (tree-* = full type slice).

## Lock (Host GO 2026-09-27 PT)

| Item | Lock |
|------|------|
| Routes | GET /api/v1/tree-mail + GET /api/v1/tree-todo only |
| Query | ?limit= default **50** (clamp 1..500); ?cursor=; ?depth= default **1**; ?parent_id= as 	ype:id |
| Omit-all-queries | progressive defaults (limit=50, depth=1) -- **not** full-slice |
| Response | 	rees + 
ext + mill; nodes include has_children (
gt > lft+1) |
| Cursor | opaque orest|type:id|lft |
| Stream | nest-set ORDER BY lft within forest; first paint depth<=1; expand = **direct children** only |
| Floor parts=trees | **sticky follow** -- not this shot |
| Validator | depth-cap first page; cursor next; parent_id expand; omit-queries not fat |

## Files

- gent_coord/server/records/floor.py - progressive helpers + 1_tree_mail / 1_tree_todo
- gent_coord/server/middleware.py - pass limit/cursor/depth/parent_id into tree builders
- gent_coord/server/records/tree.py - has_children on pack_trees nodes
- 	ests/server/test_v1_trees_progressive.py
- docs/claims/WALL-CONTRACT-v1-trees-progressive.md + this claim

## Claims with path:lines (Builder)

| Claim | Path |
|-------|------|
| Depth default + parsers | gent_coord/server/records/floor.py:212-260 (TREE_DEPTH_DEFAULT, parse_tree_depth, parse_tree_parent_id) |
| Stream + cursor + page | gent_coord/server/records/floor.py:275-380 (_tree_stream_cursor_key, _flatten_trees_stream, page_trees_progressive) |
| v1 tree-mail progressive | gent_coord/server/records/floor.py:1599-1622 |
| v1 tree-todo progressive | gent_coord/server/records/floor.py:1625-1648 |
| Middleware wire | gent_coord/server/middleware.py:1330-1353 (1_tree_mail/1_tree_todo + depth/parent_id) |
| has_children nest-set | gent_coord/server/records/tree.py:213 (
gt > lft + 1) |
| Tests | 	ests/server/test_v1_trees_progressive.py (7) |

## Follow

1. Measure v1 tree-mail / tree-todo on live Wall host
2. Floor parts=trees progressive (sticky) if GO
3. wall-ui expand/scroll claim

## Out of scope

Push, mill-wall recycle, SP apply, floor parts=trees progressive, wall_ui glass edits, invent alternate cursor schemes.

## Roles only

Builder / wall-ui / Operator / Validator / Host -- no personal names or home paths.

## Mill todos

| id | need_id | Status |
|----|---------|--------|
| 55 | v1-page-trees-progressive | **RC Ready** (v1 tree-mail + tree-todo this shot) |
