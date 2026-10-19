# Claim - Builder Loop-2 v1 mailbox/todos limit+cursor

Status: **local WIP** on `claim/floor-v1-parts`. Committed locally only. Not pushed. No mill-wall recycle (Operator).

Parent: lean list truncate (`fca60f2` / `WALL-CONTRACT-lean-mailbox-todos`) + cold-SQL Loop-2.
Evidence: `~/.mill/evidence/builder-v1-limit-cursor-20260926/`
Contract: `docs/claims/WALL-CONTRACT-v1-limit-cursor.md` (universal shape + follow matrix).
Widen: host - page limit applies to ALL dense content panes eventually; trees PARK progressive.

## Lock (shipped N=50)

| Item | Lock |
|------|------|
| Routes | `GET /api/v1/mailbox` + `GET /api/v1/todos` |
| Query | `?limit=` default **50** (clamp 1..500); `?cursor=` last row id |
| Response | `next` cursor or `null`; keep lean `*_trunc` flags |
| Paging | Python after existing `mill_mail_list` LIMIT 500 (no SP change) |
| Todos stream | needs then issues; page split back into those keys |
| Trees | **PARK** - progressive depth/page N=50 later |
| Validator | first page limit=50 ≪50KB; warm p95 <=200ms on this machine; cursor next works |

## Files

- `agent_coord/server/records/floor.py` - `parse_list_page`, `page_by_cursor`; `v1_mailbox` / `v1_todos` page + `next`
- `agent_coord/server/middleware.py` - pass limit/cursor into v1 mailbox/todos
- `tests/server/test_v1_limit_cursor.py`
- `docs/claims/WALL-CONTRACT-v1-limit-cursor.md` (universal + matrix) + this claim
- `docs/claims/WALL-CONTRACT-lean-mailbox-todos.md` - paging pointer
- Evidence samples + measure-local-mill.txt

## Measure (this machine checkout DB path, 2026-09-26 PT)

| Call | resp_b | n | warm ms | next |
|------|--------|---|---------|------|
| mailbox limit=50 | ~21KB | 50 | ~19 | non-null |
| todos limit=50 | ~25KB | 50 | ~19 | non-null |
| mailbox cursor page2 | ~16KB | 50 | ~18 | non-null |
| todos cursor page2 | ~23KB | 50 | ~18 | non-null |

Live Wall pre-recycle baseline (full lists, no limit yet): mailbox ~55KB/155 ~50ms; todos ~179KB/486 ~65ms.

## Follow (under #40 / wall-ui-perf-rebuild)

Same universal `?limit=&cursor=` + `next`.

1. `/api/floor?parts=mail` ? **SHIPPED** (see CLAIM-floor-limit-other-panes)
2. `/api/floor?parts=todos` ? **SHIPPED**
3. `/api/floor?parts=agents` ? **SHIPPED**
4. `/api/floor?parts=scores` ? **SHIPPED**
5. `/api/floor?parts=holds|watchers|events` ? **SHIPPED**
6. `/api/activity` ? **SHIPPED**
7. `/api/office-glance` only if fat after measure ? open
8. Trees progressive depth/page N=50 (**PARK** #55 ? explicit)

## Out of scope

Push, mill-wall recycle, SP apply, progressive trees implement (wall_ui infinite-scroll: see CLAIM-wall-ui-limit-cursor-scroll.md).

## Roles only

Builder / wall-ui / Operator / Validator - no personal names or home paths.

## Mill todos

| id | need_id | Status |
|----|---------|--------|
| 49 | v1-page-floor-mail | **done** (CLAIM-floor-limit-other-panes) |
| 50 | v1-page-floor-todos | **done** |
| 51 | v1-page-floor-agents | **done** |
| 52 | v1-page-floor-scores | **done** |
| 53 | v1-page-floor-session-parts | **done** |
| 54 | v1-page-activity | **done** |
| 55 | v1-page-trees-progressive | **PARK** |
| 40 | wall-ui-perf-rebuild (cloud-mill) | note only ? GitHub hang blocked |

GitHub #40 comment hang: blocked (no gh; MCP needsAuth).
