# Claim - SCORE book KPI: activities per hour

Status: **local WIP** on `claim/floor-v1-parts`. Committed locally only. Not pushed. Not pack/PyPI.

Parent tip: wow161 wall_perf timings (`959aa3a`). Score tick book path only (900s loop). No wall_ui. No Server-Timing. No floor `?timings=`. No hot-path tax on `/api/floor` or `/api/v1`.

## Roles only

No personal identifiers in commits, Claims, or docs - roles only (host, desk, human, agent, ROLE_Admin, PROJ_Office).

## Lock

Publish a human SCORE KPI for **activities per hour** into the existing `score_tick` -> `agent_kpi` **book** path (`WINDOW_S=3600` already). Prefer SQL `COUNT` of `activity` rows touched in the last hour over a new SoR table. Reuse `BOOK_SQL` / `measure_book` / tick `publish` (same pattern as `todo.shipped` / `todo.open` / `join.n`). Informational throughput - target empty string like `mill-wall.api_n` / `mill-wall.floor_n` (not a red target of 0). Opt-in via `mill score-add` (book rows only update when a score row already exists).

## KPI

| Field | Value |
| --- | --- |
| Name | `mill-office.activities` |
| Formula | `SELECT COUNT(*) FROM activity WHERE updated >= NOW(6) - INTERVAL 3600 SECOND` (`WINDOW_S`) |
| Meaning | Entity rows in `activity` touched in the last hour (mail/todo/join/hold/score/name) |
| Target | `""` (informational; no alarm) |
| Owner / roster | `ROLE_Admin` / `PROJ_Office` |
| Cadence | `score_tick` every `EVERY_S=900`; measure window `WINDOW_S=3600` |
| Opt-in | `mill score-add mill-office.activities` (mint score row; tick then refreshes Last) |

## What landed

1. **`agent_coord/server/score_tick.py`** - `WINDOW_S`/`EVERY_S` above `BOOK_SQL`; add `mill-office.activities` COUNT; `BOOK_TARGET` empty for this KPI; `publish` + `score_add` use `BOOK_TARGET` so `""` is preserved.
2. **`tests/server/test_score_tick.py`** - formula / `BOOK_TARGET` / `measure_book` fake cursor / publish-target path.
3. **This claim**.

## Evidence (path:lines)

- Book KPI + formula: `agent_coord/server/score_tick.py:65-86` (`WINDOW_S`, `BOOK_SQL["mill-office.activities"]`, `BOOK_TARGET`)
- Measure opt-in: `agent_coord/server/score_tick.py:352-370` (`measure_book`)
- Opt-in mint: `agent_coord/server/score_tick.py:373-406` (`score_add` prefers `BOOK_TARGET`)
- Tick publish: `agent_coord/server/score_tick.py:473-481` (book loop `BOOK_TARGET.get(kpi, TARGET)`)
- Tests: `tests/server/test_score_tick.py:125-190` (`test_book_activities_kpi_formula`, `test_measure_book_activities_window`, `test_publish_book_activities_empty_target`)

## Glance (host / Operator)

1. Opt in once: `mill score-add mill-office.activities` (or recycle after mint).
2. Run `mill score-tick --once` (or wait for mill-score 900s loop).
3. Floor `/api/floor?parts=scores` (or SCORE v1) shows `mill-office.activities` Last = COUNT in last hour; target blank.
4. Confirm no change to `/api/floor` or `/api/v1` request path latency (KPI is score_tick only).

## Out of scope

- wall_ui chip / Loop-3 paint (Recommended next for Wall)
- Push / pack / PyPI / Playwright / mill-wall recycle
- Server-Timing or floor `?timings=`
- New activity/event SoR table
- Hot-path counters on floor/v1

## Recommended next (Wall / Loop-3)

SCORE strip/chip: show **`mill-office.activities`** as "activities/h" (informational; no red when non-zero). Read from existing floor scores/kpis - no Loop-2 glass.
