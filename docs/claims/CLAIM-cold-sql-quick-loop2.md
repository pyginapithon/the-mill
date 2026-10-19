# Claim - Builder Loop-2 cold-SQL package (mailbox N+1 / warm / v1 fp / connector knobs)

Status: **local WIP** on `claim/floor-v1-parts`. Committed locally only. Not pushed. No mill-wall recycle (Operator).

Parent: wall-ui-perf-rebuild (#40 cloud-mill) + floor v1 parts measure (CLAIM-floor-v1-parts).
Evidence: `~/.mill/evidence/builder-cold-sql-quick-20260926/`

## Lock (Host GO Loop-2)

| Lever | Action |
|-------|--------|
| Mailbox N+1 | Python-only: group dests from `mill_mail_list` JOIN; batch `tree_crumbs` - **no SP change** |
| Lifespan warm | Open all pool slots + background `build_rooms` + `build_mailbox` after listen |
| v1 empty-on-match fp | `/api/v1/mailbox` + `/api/v1/todos` honor `?fp=`; skip body on hit; document client `?fp=` |
| Connector knobs | Optional `use_pure` / `compress` / `buffered` with safe defaults; HOST.md |
| wall-ui Rooms stagger | **ASSIGN** wall-ui (do not build here): rooms/tree first, mailbox after - not Promise.all trio |
| PARK | lean mailbox body-on-open; front httpd restore; uvicorn multi-worker; progressive trees |

## Files

- `agent_coord/server/records/mail.py` - `group_list_rows`, `tree_crumbs_batch`
- `agent_coord/server/records/floor.py` - `build_mailbox` + floor mail path collapse; `v1_mailbox` / `v1_todos` client_fps
- `agent_coord/server/middleware.py` - pass `parse_floor_fps(qs)` into v1 mailbox/todos
- `agent_coord/server/records/db.py` - `warm_pool` opens all slots; `warm_read_paths`; buffered cursor
- `agent_coord/server/asgi.py` - background warm paths after listen
- `agent_coord/config.py` - connector knobs + `mysql_cursor_kwargs`
- `docs/install/HOST.md` - knobs + warm behavior
- Tests: `tests/server/test_cold_sql_mailbox_fp.py`, `tests/client/test_mysql_connector_knobs.py`

## Client ?fp= (document; wall may wire later)

```
GET /api/v1/mailbox?project=the-mill&fp=mail:<16hex>
GET /api/v1/todos?project=the-mill&fp=todos:<16hex>
```

Hit: empty `mailbox` / `needs`+`issues`, same `fp` echoed. Miss / absent: full body + fp.

## Out of scope

Push, service recycle, SP apply, wall_ui edits, progressive trees, lean body-on-open.

## Roles only

Commits / docs / todos use Builder / wall-ui / Operator / Validator - no personal names or home paths.

## UNPARK lean list (Host GO via wall-ui)

Shipped with this package (no longer parked):

| Lever | List/poll | Open/detail |
|-------|-----------|-------------|
| Mailbox | ody <= 256; ody_trunc when clipped | GET /api/v1/mail/{id} -> mail full |
| Todos | doing/detail <= 256; doing_trunc / detail_trunc | GET /api/v1/todo/{id} -> 	odo full |

Contract + samples: docs/claims/WALL-CONTRACT-lean-mailbox-todos.md and evidence sample-v1-*-lean.json / sample-v1-*-one.json.

