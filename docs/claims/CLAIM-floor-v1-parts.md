# Claim - floor v1 part measure endpoints (Host GO B)

Status: **RC Ready** on `claim/floor-v1-parts`. Local commit only. Not pushed. Not PyPI.

**Kill-slice set complete** for isolates: agents / scores / holds / watchers / events / names (SESSION / SCORE / Glossary). `/api/floor` aggregator remains for sticky fallback.

Parent DESIGN: `~/.mill\evidence\builder-floor-parts-split-20260926\DESIGN.md`  
Evidence: same folder (samples + WALL-CONTRACT + SAMPLE-CURLS).  
Base: `claim/floor-fingerprint` @ `b337b2d` (keeps `/api/floor` + fp aggregator).

## Lock (Host GO B unanswered -> locked)

| Item | Lock |
|------|------|
| Scope | `?project=` / `?projects=` first (lan/role follow) |
| `/rooms` | lean mail roots only (`type=mail` AND `lft=1`; **no bodies**) |
| timings | only when `?timings=1` -> `{timings:{sql_ms,resp_b,n}}` |
| Mail N+1 | **collapsed Loop-2** - group mill_mail_list JOIN dests + batch tree_crumbs (CLAIM-cold-sql-quick-loop2) |
| Aggregator | `GET /api/floor` + `parts=` + `fp` unchanged |
| Surface | GET-only; **no wall_ui edits** |
| Trees | progressive trees **PARKED**; tree-* = full type slice |

## Routes (wall-ui locked names)

| Route | Builder | Payload keys (floor subset / thin) |
|-------|---------|--------------------------------------|
| `GET /api/v1/rooms` | `v1_rooms` | `trees` = mail@lft=1 forests, lean nodes (`title=""`) |
| `GET /api/v1/mailbox` | `v1_mailbox` | `mailbox`, `desk_unread`, `fp.mail` (N+1 collapsed; empty-on-match `?fp=`) |
| `GET /api/v1/tree-mail` | `v1_tree_mail` | `trees` nodes with `type=mail` only |
| `GET /api/v1/tree-todo` | `v1_tree_todo` | `trees` nodes with `type=todo` only |
| `GET /api/v1/todos` | `v1_todos` | `needs`, `issues`, `fp.todos` |
| `GET /api/v1/holds` | `v1_holds` | `locks`, `fp.holds`, `next` (empty-on-match `?fp=`) |
| `GET /api/v1/watchers` | `v1_watchers` | `watchers`, `fp.watchers`, `next` (empty-on-match `?fp=`) |
| `GET /api/v1/events` | `v1_events` | `events`, `fp.events`, `next` (empty-on-match `?fp=`) |
| `GET /api/v1/names` | `v1_names` | `catalog`, `fp.names`, `next` (empty-on-match `?fp=`; floor part `names`) |

All responses stamped with top-level **`mill`** via `_json` / `stamp_mill`.  
Path rewrite: `/api/v1/X` -> `/api/X` (existing middleware); both work.

## Files

- `agent_coord/server/middleware.py` - register v1 part GET handlers (rooms..names) + `api.v1.*` perf_log
- `agent_coord/server/records/floor.py` - `build_*` + `v1_*` isolates (extract, not copy of floor assemble)
- `agent_coord/server/records/tree.py` - `mail_room_root_rows` lean SQL
- `tests/server/test_floor_v1_parts.py` - ASGI + builder unit tests
- `docs/claims/CLAIM-floor-v1-parts.md` - this claim
- Evidence: `sample-*.json`, `SAMPLE-CURLS.md`, `WALL-CONTRACT.md`

## Tests

```text
pytest tests/server/test_floor_v1_parts.py -q
# 8 passed (local). pytest-of-host symlink cleanup may WinError 5 after pass - ignore.
```

Throwaway smoke: ASGI TestClient hit all five `?project=demo&timings=1` -> 200 + mill + timings; bare `/api/floor` still 400.

## Acceptance map

| # | Criterion | Result |
|---|-----------|--------|
| A1 | Curl each route alone; ms + resp_b | handlers log `api.v1.*` + optional timings |
| A2 | `/api/floor?parts=mail,trees,todos` still works | floor path untouched |
| A3 | Wall poll still `/api/floor` | no wall_ui edit |
| A4 | Measure table ready | samples under evidence |
| A5 | No progressive trees | full type slice |
| A6 | No push | local only |

## Out of scope / follow

- lan/role on v1, office routes, mail N+1 collapse SP, progressive trees, push/deploy, wall_ui wire

## Ping-ready for wall-ui

Branch `claim/floor-v1-parts`. Contract + samples in evidence folder. Wire against `/api/v1/{rooms,mailbox,tree-mail,tree-todo,todos}?project=...` (+ `&timings=1` for CLI). Keep polling `/api/floor` for the Wall.

