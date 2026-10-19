# Claim - A1 agent value: wake -> first day-one verb

Status: **local WIP** on `claim/floor-v1-parts`. Committed locally only. Not pushed. Not pack/PyPI.

Parent tip: wow162 SCORE chip activities/h (`2b3744f`). Product **activity** Shot A1 (Operator GO). No new Wall chrome. No always-on Server-Timing. No hot-path tax on `/api/floor` or `/api/v1`.

Related: cloud-mill todo **#56** (HINT TODO wake path observed on mill-perf `hint=TODO id=56`) - wake clock aligns with desk session / HINT wake -> first useful verb.

## Roles only

No personal identifiers in commits, Claims, or docs - roles only (host, desk, human, agent, ROLE_Admin, PROJ_Office).

## Lock

Measure **latency** and **mill RPC count** from desk wake to first successful day-one verb. Prefer existing mill-perf + score_tick book path (opt-in `mill score-add` like `mill-office.activities`). Smallest wire: in-process desk session stamp on first day-one ok -> one `op=wake.first_ok` mill-perf line; score_tick scrapes p50 into agent_kpi book.

## Formula

| Field | Value |
| --- | --- |
| Wake t0 | First `/ws` connect (`Hub` mark_socket up) |
| First ok | First successful day-one verb after t0: `open`/`todo`/`claim`/`assign`/`unclaim`/`note`/`pass`/`send`/`reply`/`mail-thread`/`inbox`/`hold`/`drop` |
| Latency | `(t_first_ok - t0)` wall ms on the stamp line `ms=` |
| RPC count | Count of mill RPCs after t0 through the first ok inclusive; skip `heartbeat`/`session`/`join` |
| Stamp | One per wake session: `op=wake.first_ok ms=... rpc=... desk=DESK_* verb=... ok=1` |
| KPI ms | `mill-office.wake_first_ms` = **p50** of `ms=` on `wake.first_ok` lines in `WINDOW_S=3600` |
| KPI rpc | `mill-office.wake_first_rpc` = **p50** of `rpc=` on those lines |
| Target | `""` (informational; no red alarm) |
| Owner / roster | `ROLE_Admin` / `PROJ_Office` |
| Cadence | score_tick every `EVERY_S=900` |
| Opt-in | `mill score-add mill-office.wake_first_ms` and/or `mill score-add mill-office.wake_first_rpc` |

## What landed

1. **`agent_coord/server/wake_first.py`** - DAY_ONE_OK_VERBS; mark_wake / note_rpc / clear_wake; emit `wake.first_ok`.
2. **`agent_coord/server/push.py`** - mark_wake on `/ws` up; clear on down.
3. **`agent_coord/server/api/mill/rpc.py`** - note_rpc after dispatch + dispatch_ws (ok and fail).
4. **`agent_coord/server/score_tick.py`** - `measure_wake_first` p50; BOOK_PERF opt-in publish; score_add knows BOOK_PERF.
5. **`tests/server/test_wake_first.py`** - formula / stamp-once / p50 / empty target.
6. **This claim**.

## Evidence (path:lines)

- Stamp module: `agent_coord/server/wake_first.py`
- Connect hook: `agent_coord/server/push.py` (`_mark_join_socket`)
- RPC hooks: `agent_coord/server/api/mill/rpc.py` (`dispatch`, `dispatch_ws`)
- Scrape + book: `agent_coord/server/score_tick.py` (`measure_wake_first`, `BOOK_PERF`, publish opt-in)
- Tests: `tests/server/test_wake_first.py`

## Glance (host / Operator)

1. Opt in: `mill score-add mill-office.wake_first_ms` and `mill score-add mill-office.wake_first_rpc`.
2. Run `mill score-tick --once` (or wait mill-score 900s) after desks have stamped `wake.first_ok` in mill-perf.
3. Floor `/api/floor?parts=scores` (or SCORE v1) shows Last = p50 ms / p50 rpc; target blank.
4. Confirm no new Wall chrome and no Server-Timing on floor/v1 hot path.

## Open edges (flagged)

- **SoR subset:** stamp is in-process (mill-wall process). Restart clears un-stamped sessions; already-emitted mill-perf lines remain for scrape.
- **Multi-worker:** each mill-wall process has its own session map (same as Hub rooms).
- **HINT client wake URL** (grok-bot `/wake`) is client-side; server t0 is `/ws` connect, not the HTTP wake-hook RTT.
- **No schema change** on `join` / `activity` for first-verb columns (perf stamp only).
- Wall chip label for these KPIs = follow-on (like wow162 activities/h); out of A1.

## Out of scope

- Shot A2
- Wall UI chip / Loop-3 paint
- Push / pack / PyPI / Playwright / mill-wall recycle
- Server-Timing or floor `?timings=` always-on
- New activity/event SoR table

## Ready for Validator

Local commit + pytest green on formula tests. Operator opts in via score-add; no Wall change required to measure.
