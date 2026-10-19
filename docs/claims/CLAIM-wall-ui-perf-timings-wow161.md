# Claim - Wall UI wall_perf server timings strip (wow161)

Status: **local WIP** on `claim/floor-v1-parts`. Committed locally only. Not pushed. Not pack/PyPI. No Playwright.

Parent tip: wow160 hybrid revert (`4f22aad`). Builds on `docs/claims/CLAIM-wall-ui-perf-instrument.md` (wow137 gate).
Server wire (already exists; do not invent): `GET /api/v1/*?timings=1` -> body `timings: {sql_ms, resp_b, n}` (`agent_coord/server/middleware.py` ~1263-1315).

## Roles only

No personal identifiers in commits, Claims, or docs - roles only (host, desk, human, agent, registered machine, Wall-reachable host).

## Lock

When `?wall_perf=1` (or `localStorage.wall_perf=1`), client appends `timings=1` to `/api/v1/*` GETs, parses response `timings`, and shows an opt-in strip under the tab strip: route, client RTT, sql_ms, resp_b (and n). ZERO cost when wall_perf off (perf.js still not fetched). Do not invent Server-Timing headers or floor timings API. Do not fan-out FLOOR hybrids to v1 (wow160 lock holds). Human-readonly GET-only. No Builder SoR edits in Wall commits. No push / pack / PyPI / Playwright.

## What landed

1. **`lib/perf.js`** - `withTimingsParam` on `/api/v1/*` GET; clone+JSON parse for `timings`; `#wall-perf-strip` under `.strip-stack` (below `#strip`, above `#subnav`); console.table gains sql_ms/resp_b/n. Floor GETs still measured for client RTT/bytes only (no `timings=1`).
2. **`shell-early.js`** - `lib/perf.js?v=wow161`.
3. **`board.html`** - `shell-early.js?v=wow161` (theme/hash/perf gates).
4. **Tests** - `tests/wall/test_wall_ui_perf_timings.py` (append + parse + strip + cache-bust).
5. **This claim**.

## Evidence (path:lines)

- Append: `agent_coord/web/wall_ui/lib/perf.js` `withTimingsParam` + wrapFetch GET `/api/v1/`
- Parse + strip: `lib/perf.js` `showStrip` / `#wall-perf-strip` (route, rtt, sql_ms, resp_b, n)
- fp hit: comment only - empty part + echoed fp already visible; no new strip field
- Cache-bust: `shell-early.js` -> `lib/perf.js?v=wow161`; `board.html` `shell-early.js?v=wow161`
- Server (unchanged): `agent_coord/server/middleware.py` ~1263-1315 `want_timings` / `payload["timings"]`
- Tests: `tests/wall/test_wall_ui_perf_timings.py`

## Glance (host / Operator)

1. Recycle **mill-wall** so checkout serves this tip (optional if static wall_ui already from checkout).
2. Open Wall with `?wall_perf=1` and hard-refresh (`lib/perf.js?v=wow161`).
3. Hit SESSION / SCORE / MAIL (v1 GETs). Network: `/api/v1/...?timings=1`.
4. Strip under tab strip shows route + rtt + **sql_ms** (+ resp_b / n).
5. FLOOR Map/Timeline still `/api/floor` (no timings=1); hybrids stay wow160.

## Out of scope

- Push / pack / PyPI / Playwright / mill-wall recycle (host)
- Inventing Server-Timing or `/api/floor?timings=`
- Re-fan-out FLOOR hybrids to v1
- Builder `floor.py` / middleware edits in Wall commits
- Changing boot.js logic this ship (boot cache may remain wow160)
