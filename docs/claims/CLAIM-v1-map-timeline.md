# Claim - GET /api/v1/map and /api/v1/timeline joined Floor hybrids

Status: **RC Ready** on `claim/floor-v1-parts`. Local commit only. Not pushed. Not pack/PyPI.
Parent: wow160 revert (`CLAIM-wall-ui-floor-hybrids-revert-wow160.md`) + Host GO Loop-2 joined isolates.
Contract base: `WALL-CONTRACT-floor-v1-parts.md` + existing `_V1_PARTS` / floor part builders.

## Lock

Ship FLOOR Map / Timeline hybrids as **two** server-joined v1 isolates (one RTT each). Not one mega payload. Not client `Promise.all` of agents+mailbox. Reuse floor part builders server-side. Sticky down remains `GET /api/floor?parts=`. Human-readonly GET-only. No wall_ui glass edits (Loop-3). No push / pack / PyPI.

## Routes

| Route | Join (floor parts) | Payload keys |
|-------|--------------------|--------------|
| `GET /api/v1/map?project=` | `agents,mail` | `agents`, `mailbox`, `desk_unread`, `fp`, `next`, `parts` |
| `GET /api/v1/timeline?project=` | default `agents,events` (LAN) | `agents`, `events`, `fp`, `next`, `parts` |
| `GET /api/v1/timeline?project=&parts=agents,timeline` | `agents,timeline` (project) | `agents`, `timeline`, `fp` (agents only; timeline has no mill_fp), `next`, `parts` |

Aliases: `/api/map`, `/api/timeline` via existing `/api/v1/` rewrite.
Missing `project` / `projects` => **400** `{"error":"GET /api/v1/<name> requires ?project=","mill":"..."}`.
Optional: `?fp=agents:hex,mail:hex` / `events:hex` empty-on-match per part; `?limit=` + `?cursor=` on pageable lists inside the join; `?timings=1` -> `{timings:{sql_ms,resp_b,n}}`.

## Sample JSON shape

### map

```json
{
  "mill": "0.5.8",
  "parts": ["agents", "mail"],
  "agents": [{"id": "desk_a", "owner": "desk_a"}],
  "mailbox": [{"id": 1}],
  "desk_unread": {"desk_a": 1},
  "fp": {"agents": "<16hex>", "mail": "<16hex>"},
  "next": null
}
```

### timeline (LAN / events)

```json
{
  "mill": "0.5.8",
  "parts": ["agents", "events"],
  "agents": [{"id": "desk_a", "owner": "desk_a"}],
  "events": [{"type": "todo", "id": 7, "kind": "todo"}],
  "fp": {"agents": "<16hex>", "events": "<16hex>"},
  "next": null
}
```

### timeline (project / timeline)

```json
{
  "mill": "0.5.8",
  "parts": ["agents", "timeline"],
  "agents": [{"id": "desk_a", "owner": "desk_a"}],
  "timeline": [{"id": "...", "type": "todo", "n": 2, "owner": "desk_a"}],
  "fp": {"agents": "<16hex>"},
  "next": null
}
```

## Evidence (path:lines)

- Builders: `agent_coord/server/records/floor.py` `v1_map` / `v1_timeline` (reuse `build_agents`, `build_mailbox`, `build_events`, `_timeline`, `apply_floor_list_page`)
- Register: `agent_coord/server/middleware.py` `_V1_PARTS` keys `map` / `timeline` + pageable/fp/`parts=` pass-through for `v1_timeline`
- Tests: `tests/server/test_v1_map_timeline.py`
- Floor aggregator unchanged: sticky `GET /api/floor?parts=`

## Glance curls

```bash
curl -sS "http://127.0.0.1:8765/api/v1/map?project=the-mill&timings=1"
curl -sS "http://127.0.0.1:8765/api/v1/timeline?project=the-mill&timings=1"
curl -sS "http://127.0.0.1:8765/api/v1/timeline?project=the-mill&parts=agents,timeline&timings=1"
# 400 without project:
curl -sS "http://127.0.0.1:8765/api/v1/map"
```

## Files

- `agent_coord/server/records/floor.py` - `v1_map`, `v1_timeline`
- `agent_coord/server/middleware.py` - `_V1_PARTS` + handler kwargs (map/timeline only hunks)
- `tests/server/test_v1_map_timeline.py` - ASGI + builder unit tests
- `docs/claims/CLAIM-v1-map-timeline.md` - this claim

## Tests

```text
python -m pytest tests/server/test_v1_map_timeline.py -q
```

## Out of scope

- wall_ui Loop-3 glass consume
- Removing `/api/floor` aggregator
- lan/role scope on v1 map/timeline
- Push / pack / PyPI / Playwright

## Ping-ready for wall-ui

Branch `claim/floor-v1-parts`. Wire FLOOR Map -> `/api/v1/map?project=...` and Timeline -> `/api/v1/timeline?project=...` (+ `&parts=agents,timeline` for project style). Sticky down stays `/api/floor?parts=`. Merge keys match floor (`agents` + `mailbox`|`events`|`timeline`).
