# WALL-CONTRACT - progressive trees (depth-cap + limit/cursor)

Status: **Host GO / implement** -- locked defaults below. Builder ships v1 tree-mail + tree-todo only; floor `parts=trees` sticky follow.
Branch: `claim/floor-v1-parts`. Audience: Builder (v1 routes) + wall-ui (expand/scroll). Date: 2026-09-27 PT.
Parent PARK: `WALL-CONTRACT-v1-limit-cursor.md` trees PARK section; mill todo **#55** `v1-page-trees-progressive`.
Prior full slice: `WALL-CONTRACT-floor-v1-parts.md` (tree-mail / tree-todo = full type slice, no cursor).
Protocol nest-set: `docs/protocol/tree.md` (Celko; `ORDER BY lft`; depth from ancestors).

## Intent (GO question, not code)

Dense panes already ship universal `?limit=50&cursor=` + response `next` (mailbox, todos, floor parts, activity). Trees stay fat today (`v1_tree_mail` / `v1_tree_todo` -> `build_trees_typed` full type slice; middleware else-branch, **no** limit/cursor). Progressive trees should **reuse that same paging shape**, not invent a new protocol -- only add depth-cap first paint + expand-by-parent.

## Proposed universal shape (mirror dense-pane N=50)

```
GET /api/v1/tree-mail?project=<slug>&limit=50&depth=1
GET /api/v1/tree-mail?project=<slug>&limit=50&cursor=<opaque>
GET /api/v1/tree-mail?project=<slug>&parent_id=<type:id>&limit=50
```

Same for `/api/v1/tree-todo`. Aliases `/api/tree-mail` / `/api/tree-todo` via existing rewrite.

| Query | Default | Notes |
|-------|---------|-------|
| `limit` | **50** | Same clamp 1..500 via `parse_list_page`. Invalid -> 50. |
| `cursor` | omit (first page) | Opaque string of last **stream** key from prior page (nest-set order). |
| `depth` | **1** | First-paint max nest depth (`node.depth <= depth`). Only on root stream (no `parent_id`). |
| `parent_id` | omit | Expand: page **direct children** of that node. Format `type:id` (e.g. `mail:101` / `todo:5`). |

Response adds (aligned with v1 limit/cursor contracts):

| Field | Meaning |
|-------|---------|
| `trees` | Same forest shape as today (`name`, `hidden`, `nodes[]` with `type/id/lft/rgt/depth/title/status/who/roster_id`) |
| `next` | Opaque cursor for following page of the **same stream**, or **`null`** when exhausted |
| `mill` | Stamp (unchanged) |

Unknown/stale cursor -> empty `trees` + `next=null` (client resets), same as dense panes.

### Stream order (nest-set, not invent)

Flatten visible nodes across forests in existing glance order:

1. Forest order = current `pack_trees` / `_floor_trees` order (name / `ORDER BY n.name, t.lft`).
2. Within a forest: nest-set **`ORDER BY lft`**.
3. First paint filter: keep nodes with `depth <= depth` (GO default **1** = roots + one child level).
4. Page that filtered stream with `page_by_cursor` (or nest-set-aware sibling) -> `limit` + opaque `next`.

Cursor key (**locked**): opaque `forest_name|type:id|lft` of last streamed node in nest-set order.

### Expand children (`parent_id`)

```
GET /api/v1/tree-mail?project=<slug>&parent_id=mail:101&limit=50
GET /api/v1/tree-mail?project=<slug>&parent_id=mail:101&limit=50&cursor=<next>
```

- Resolve parent in project-scoped trees; page **direct children** only (nest-set: immediate descendants, depth = parent.depth+1), same `limit`/`cursor`/`next`.
- Response still `trees` (one forest subset or the forest that owns the parent) + `next`.
- Do **not** invent a separate expand path name; same route + query.

Node hint for wall-ui (**locked**): `has_children: true|false` from nest-set `rgt > lft+1`.

## Surfaces (shot order)

| Surface | Status under this DRAFT | Notes |
|---------|-------------------------|-------|
| `GET /api/v1/tree-mail` | **This shot** | Add limit/cursor/depth/parent_id; keep keys `trees` + add `next` |
| `GET /api/v1/tree-todo` | **This shot** | Same |
| `/api/floor?parts=trees` | **Sticky follow** | Not this shot; mirror after v1 tree-* measure |
| `GET /api/v1/rooms` | Out of scope | Already lean mail@lft=1 roots |

Compat (**locked**): calls with **no** `limit`/`cursor`/`depth`/`parent_id` **default into progressive** (limit=50, depth=1). Breaking for measure curls that expected full slice.

## Code anchors (Builder)

| Item | Path |
|------|------|
| Route map | `agent_coord/server/middleware.py` `_V1_PARTS` `tree-mail`/`tree-todo` -> `v1_tree_mail`/`v1_tree_todo` |
| Builders (full slice, no page) | `agent_coord/server/records/floor.py` `v1_tree_mail` / `v1_tree_todo` -> `build_trees_typed` |
| Nest-set pack | `agent_coord/server/records/tree.py` `pack_trees` (`ORDER BY lft`, depth from ancestors) |
| Page helpers | `floor.py` `parse_list_page`, `page_by_cursor` |
| PARK matrix | `docs/claims/WALL-CONTRACT-v1-limit-cursor.md` |

Middleware today: tree-mail/todo hit the **else** branch (no `parse_list_page`) -- intentional until this GO.

## Wall-ui consume (later claim; not this draft)

1. First paint / poll: `?limit=50&depth=<GO>` (no cursor). Remember `next`.
2. Near end of outline: if `next` non-null, append page (dedupe by `type:id` within forest).
3. Expand click: `?parent_id=<type:id>&limit=50`; splice children under parent; page with `next`.
4. `next=null` -> stop that stream.

## Out of scope this shot

- Server implementation, SP changes, mill-wall recycle, push.
- New REST path names / WebSocket tree protocol / invent alternate cursor schemes.
- wall_ui glass edits (separate wall-ui claim after Builder ship).
- Progressive rooms, office-glance, glossary.

## Host GO locks (2026-09-27 PT)

1. **First-paint depth:** `depth<=1` (roots + one child level).
2. **Default when queries omitted:** force progressive defaults (`limit=50`, `depth=1`) -- **not** full-slice compat.
3. **`parent_id` format:** `type:id` (e.g. `mail:101` / `todo:5`).
4. **Cursor opacity key:** `forest|type:id|lft`.
5. **`has_children` on nodes:** yes (`rgt > lft+1`).
6. **Floor `parts=trees`:** sticky follow -- **not** this shot.
7. **Expand depth:** direct children only.

## Roles only

Builder / wall-ui / Operator / Validator / Host -- no personal names or home paths.

## Mill todo

| id | need_id | Status |
|----|---------|--------|
| 55 | v1-page-trees-progressive | **Host GO / implement** (this shot: v1 tree-mail + tree-todo) |
