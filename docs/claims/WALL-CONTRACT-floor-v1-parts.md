# WALL-CONTRACT - floor v1 part measure endpoints

Status: Builder SoR on `claim/floor-v1-parts`. Wall glass separate (no wall_ui in this claim).
Date: 2026-09-26 PT.
Parent: DESIGN.md (floor parts split) + Host GO B locks.

## Request

```
GET /api/v1/rooms?project=<slug>
GET /api/v1/mailbox?project=<slug>
GET /api/v1/tree-mail?project=<slug>
GET /api/v1/tree-todo?project=<slug>
GET /api/v1/todos?project=<slug>
```

Aliases: `/api/rooms` etc. (middleware rewrites `/api/v1/` -> `/api/`).
Optional: `projects=` comma list (same as floor). **First ship: project scope only** (no lan/role).
Optional: `timings=1` -> add `timings` object (see below).

Missing `project` / `projects` ⇒ **400** `{"error":"GET /api/v1/<name> requires ?project=","mill":"..."}`.

## Response (always JSON + mill stamp)

Top-level always includes `"mill": "<pack version>"` (and usually `version`/`at`/`node`/`parts`).

### rooms

Lean mail room roots only (`WHERE type='mail' AND lft=1`). **No letter bodies.**

```json
{
  "mill": "0.5.6",
  "parts": ["rooms"],
  "trees": [
    {
      "name": "TREE_...",
      "hidden": false,
      "nodes": [
        {"type": "mail", "id": 101, "lft": 1, "rgt": 6, "depth": 0, "title": "", "status": "mail", "who": "", "roster_id": "..."}
      ]
    }
  ]
}
```

Key reused: `trees` (subset / lean). Room identity = forest `name` (TREE_*).

### mailbox

Full mailbox isolate (same enrich as floor mail part: list + N× to_list + N× tree_crumbs - **not collapsed this ship**).

```json
{
  "mill": "0.5.6",
  "parts": ["mail"],
  "fp": {"mail": "<16hex>"},
  "mailbox": [ /* public_mail rows with bodies */ ],
  "desk_unread": {"desk": 1}
}
```

### tree-mail / tree-todo

Full slice of glance trees filtered to `type=mail` or `type=todo` (not progressive / no cursor).

```json
{
  "mill": "0.5.6",
  "parts": ["trees"],
  "trees": [ /* forests; nodes only of that type */ ]
}
```

### todos

```json
{
  "mill": "0.5.6",
  "parts": ["todos"],
  "fp": {"todos": "<16hex>"},
  "needs": [ /* open/claimed cards */ ],
  "issues": [ /* parked */ ]
}
```

### timings (opt-in)

`?timings=1` adds:

```json
"timings": {"sql_ms": 12.4, "resp_b": 1234, "n": 5}
```

`n` = primary row count (mailbox len / needs+issues / trees forests).

## Compat (must not break)

- Wall keeps `GET /api/floor?...&parts=...&fp=...` - unchanged aggregator + empty-on-match fp.
- Do not invent alternate path names beyond the five locked above.
- Progressive trees PARKED.

## Client rules (Wall - later wire)

1. Measure / isolate curls may hit `/api/v1/*` alone.
2. Live Wall navigation/poll stays on `/api/floor` until a separate wall-ui claim.
3. Field keys above are the contract; do not rename (`mailbox`/`trees`/`needs`/`issues`/`fp`/`mill`).

## Out of scope

lan/role v1, follow routes (agents/scores/holds/office), mail N+1 SP collapse, progressive trees, push.
