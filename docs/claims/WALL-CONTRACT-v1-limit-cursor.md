# WALL-CONTRACT ? dense list limit + cursor (universal)

Status: Builder SoR on `claim/floor-v1-parts` (Loop-2).
Audience: wall-ui (infinite scroll on every dense pane). Date: 2026-09-26 PT.
Evidence: `~/.mill/evidence/builder-v1-limit-other-panes-20260926/`
Parent lean SoR: `WALL-CONTRACT-lean-mailbox-todos.md` (row trunc + detail-on-open).
Prior shot: `~/.mill/evidence/builder-v1-limit-cursor-20260926/` (v1 mailbox/todos).

## Universal shape (reuse everywhere)

```
GET <list-route>?project=<slug>&limit=50&cursor=<id>
```

| Query | Default | Notes |
|-------|---------|-------|
| `limit` | **50** | Clamped 1..500. Invalid ? 50. |
| `cursor` | omit (first page) | Opaque string of the **last row cursor key** from the prior page (usually row `id`). |

Response adds:

| Field | Meaning |
|-------|---------|
| `next` | Cursor for the following page, or **`null`** when no more rows |

Unknown/stale cursor ? empty page + `next=null` (client resets to first page).

Wall-ui infinite scroll (any pane):

1. First paint / poll: `?limit=50` (no cursor). Remember `next`.
2. Near end: if `next` non-null, `?limit=50&cursor=<next>`; **append** (dedupe by `id`); replace `next`.
3. `next=null` ? stop.

Helpers live in `floor.py`: `parse_list_page`, `page_by_cursor`, `apply_floor_list_page`, `page_activity_rows`.

## Shipped ? v1 isolates (prior)

| Route | Stream order | Notes |
|-------|--------------|-------|
| `GET /api/v1/mailbox` | mail id DESC (SP) | lean `body_trunc`; `desk_unread`+`fp.mail` = **full** set |
| `GET /api/v1/todos` | **needs then issues** | lean `doing_trunc`/`detail_trunc`; page split back into those keys; `fp.todos` full |

Also still honor: `?fp=` empty-on-match, `?timings=1`, detail routes `/api/v1/mail/{id}` + `/api/v1/todo/{id}`.

## Shipped this shot ? floor parts + activity (N=50)

| Route | Stream / cursor key | Notes |
|-------|---------------------|-------|
| `GET /api/floor?parts=mail` | mailbox id | `desk_unread` / glance / `fp` from **full** set before page |
| `GET /api/floor?parts=todos` | needs then issues (id) | same split as v1 todos |
| `GET /api/floor?parts=agents` | agent `id` (join id; lan/role falls back to `owner`) | seats |
| `GET /api/floor?parts=scores` | score `id` (or `owner\|kpi\|roster_id`) | KPI rows (`kpis`) |
| `GET /api/floor?parts=holds` | hold `id` (or `resource\|owner\|roster_id`) | locks |
| `GET /api/floor?parts=watchers` | `type:id` | grouped watchers |
| `GET /api/floor?parts=events` | `type:id` | activity events |
| `GET /api/activity` | stamped opaque row `id` | feed `rows` + `next` |

`?cursor=` applies to the **primary** pageable part (first of mail?todos?agents?scores?holds?watchers?events present in `parts=`). Prefer a single `parts=` value for infinite scroll. Multi-part requests still clamp each dense list to `limit` (first page for non-primary).

## PARK ? trees

| Route | Status |
|-------|--------|
| `GET /api/v1/tree-mail` | **PARK** ? progressive trees get depth/page N=50 later |
| `GET /api/v1/tree-todo` | **PARK** ? same |
| `/api/floor?parts=trees` | **PARK** ? follows progressive trees (#55) |

Do not invent a tree cursor protocol in this shot.

## Follow matrix (dense panes Wall hits)

Same `?limit=&cursor=` + `next` shape.

| Surface / pane | Endpoint(s) | Status |
|----------------|-------------|--------|
| MAIL list / Rooms mailbox | `/api/v1/mailbox` | **SHIPPED** |
| TODO Nest/List/Board cards | `/api/v1/todos` | **SHIPPED** |
| MAIL/TODO trees | `/api/v1/tree-mail`, `/api/v1/tree-todo`, floor `parts=trees` | **PARK** progressive (#55) |
| MAIL Rooms roots | `/api/v1/rooms` | lean already (roots only); page later if needed |
| Floor aggregator mail | `/api/floor?parts=mail` | **SHIPPED** |
| Floor aggregator todos | `/api/floor?parts=todos` | **SHIPPED** |
| SESSION seats | `/api/floor?parts=agents` | **SHIPPED** |
| SCORE book | `/api/floor?parts=scores` | **SHIPPED** |
| SESSION leases / watch / history | `/api/floor?parts=holds\|watchers\|events` | **SHIPPED** |
| SESSION activity feed | `/api/activity?project=&window=` | **SHIPPED** |
| Office glance | `/api/office-glance` | open ? thin summary; page only if fat |
| Glossary | `/api/floor?parts=names` | open if fat |
| Strip / rows | `/api/strip`, `/api/rows` | likely already lean; measure before page |

## Out of scope this commit

mill-wall recycle; SP apply; push; progressive tree depth protocol.

## Wall-ui consume

v1 mailbox/todos scroll: CLAIM-wall-ui-limit-cursor-scroll.md (wow145).
Floor parts + activity infinite scroll: open wall-ui follow (after Operator recycle).

## Floor events paging order (Major fix 2026-09-26)

Floor events: page after board_view TTL/fixture filter - see CLAIM-floor-limit-other-panes.
