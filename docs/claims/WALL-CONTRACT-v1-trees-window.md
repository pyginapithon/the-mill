# WALL-CONTRACT - tree-mail/todo ?window= (nest-mail-filter)

Status: **Host GO / implement** -- locked defaults below. Builder ships v1 tree-mail + tree-todo only; floor `parts=trees` sticky follow **not** this shot.
Branch: `claim/floor-v1-parts`. Audience: Builder (v1 routes) + wall-ui (All | 1d | 1w | 30d chips). Date: 2026-09-27 PT.
Parent: progressive trees Host GO (`WALL-CONTRACT-v1-trees-progressive.md` / mill todo **#55**). Mill card **#58** `nest-mail-filter-windows`.

## Intent

Dense panes already page with limit/cursor. Progressive trees (#55) keep forests fat across time. Nest panes need a **time window** so wall-ui can show All / last day / week / 30d without inventing a new route. Filter by **last TREE activity** under each forest (activity.updated on any nest-set node), **not** mailbox-only `mail.created`.

## Query (locked)

```
GET /api/v1/tree-mail?project=<slug>&window=1d
GET /api/v1/tree-todo?project=<slug>&window=1w&limit=50&depth=1
GET /api/v1/tree-mail?project=<slug>   # omit window = All
```

| Query | Values | Notes |
|-------|--------|-------|
| `window` | `1d` \| `1w` \| `30d` | Keep forests whose **last TREE activity** is within the window. |
| omit / empty | **All** | No time filter (today's progressive stream unchanged). |

Invalid `window` (anything else non-empty) -> **HTTP 400** with clear `error` string (e.g. `invalid window; use window=1d|1w|30d or omit for All`).

Progressive contract **unchanged**: `limit` / `cursor` / `depth` / `parent_id` / `has_children` / response `trees`+`next`+`mill`.

### Last TREE activity (not invent)

Source of truth: `activity.updated` for every nest-set row under the forest (`tree` JOIN `activity` on `(type,id)`). Forest last activity = **MAX(activity.updated)** across **all** node types on that TREE plan (mail/todo/join/hold/score/name) -- not mail.created alone, not mailbox-only timestamps.

Keep forest when `last_activity >= now - window`. Forests with no activity row (NULL max) drop out when a window is set.

Apply **before** progressive page (limit/cursor/depth/parent_id), so paging streams only kept forests.

## Surfaces

| Surface | This shot |
|---------|-----------|
| `GET /api/v1/tree-mail` | **Yes** -- add `?window=` |
| `GET /api/v1/tree-todo` | **Yes** -- same |
| `/api/floor?parts=trees` | **Sticky follow -- not this shot** |
| Aliases `/api/tree-mail` / `/api/tree-todo` | Via existing rewrite |

## Code anchors (Builder)

| Item | Path |
|------|------|
| Window parse | `agent_coord/server/records/floor.py` `parse_tree_window` |
| Forest filter | `floor.py` `filter_trees_by_window` + `v1_tree_mail` / `v1_tree_todo` |
| Last activity | `agent_coord/server/records/tree.py` `forest_last_activity` (MAX activity.updated per TREE name) |
| Middleware | `agent_coord/server/middleware.py` pass `window`; 400 on invalid |
| Schema SoR | `agent_coord/server/sql/tables.sql` `activity.updated` |

## Out of scope this shot

- Floor `parts=trees` window, pack/PyPI, push, SP apply, wall_ui glass chips.
- New window tokens beyond `1d|1w|30d`.
- Changing progressive defaults (limit=50, depth=1).

## Host GO locks (2026-09-27 PT)

1. **Surfaces:** GET /api/v1/tree-mail + /api/v1/tree-todo only.
2. **Query:** `window=1d|1w|30d`; omit = All.
3. **Semantics:** keep forests whose last TREE activity (MAX activity.updated under forest) is within window.
4. **Invalid:** 400 with clear error.
5. **Response:** same `trees` + `next` + `mill` shape.
6. **Progressive:** limit/cursor/depth/parent_id/has_children unchanged.
7. **Floor parts=trees:** sticky -- **not** this shot.

## Roles only

Builder / wall-ui / Operator / Validator / Host -- no personal names or home paths.

## Mill todo

| id | need_id | Status |
|----|---------|--------|
| 58 | nest-mail-filter-windows | **Host GO / implement** (this shot: v1 tree-mail + tree-todo) |
