# Claim - A2 agent value: wrong-verb / retry before first ok

Status: **local WIP** on `claim/floor-v1-parts`. Committed locally only. Not pushed. Not pack/PyPI.

Parent tip: A1 wake->first day-one verb stamp + book KPIs (`2c8d5a4`). Product **activity** Shot A2 (Operator GO after A1). No new Wall chrome. No always-on Server-Timing. No hot-path tax on `/api/floor` or `/api/v1`.

Related: cloud-mill todo **#56** (HINT TODO wake path observed on mill-perf `hint=TODO id=56`) - same desk session / wake clock as A1; A2 stamps friction (non-ok + same-verb retry) on the first day-one ok line.

## Roles only

No personal identifiers in commits, Claims, or docs - roles only (host, desk, human, agent, ROLE_Admin, PROJ_Office).

## Lock

Measure **non-ok mill replies** and **same-verb re-tries before first day-one ok**, stamped with the success **verb name**. Reuse A1 wake-session + mill-perf stamp (`op=wake.first_ok`); extend the line with `wrong=` / `retry=` / `verb=`. score_tick scrapes p50 into opt-in book KPIs (same `mill score-add` gate as `mill-office.wake_first_*`).

## Formula

| Field | Value |
| --- | --- |
| Wake t0 | Same as A1: first `/ws` connect (`Hub` mark_socket up) |
| First ok | Same as A1: first successful day-one verb after t0 |
| wrong | Count of **non-ok** mill RPCs after t0 through (not including) the first day-one ok; skip `heartbeat`/`session`/`join` |
| retry | Count of prior **non-ok** attempts of the **same verb** that first-ok's (after t0); other verbs' fails count in `wrong` only |
| Stamp | One per wake session (A1 line extended): `op=wake.first_ok ms=... rpc=... wrong=... retry=... desk=DESK_* verb=... ok=1` |
| KPI wrong | `mill-office.wrong_verb_n` = **p50** of `wrong=` on `wake.first_ok` lines in `WINDOW_S=3600` |
| KPI retry | `mill-office.retry_before_ok` = **p50** of `retry=` on those lines |
| Target | `""` (informational; no red alarm) |
| Owner / roster | `ROLE_Admin` / `PROJ_Office` |
| Cadence | score_tick every `EVERY_S=900` |
| Opt-in | `mill score-add mill-office.wrong_verb_n` and/or `mill score-add mill-office.retry_before_ok` |

## What landed

1. **`agent_coord/server/wake_first.py`** - session `wrong_n` + per-verb `fails`; stamp `wrong=` / `retry=`; BOOK_PERF KPIs.
2. **`agent_coord/server/score_tick.py`** - `measure_wrong_retry` p50; measure() publishes opt-in values; BOOK_PERF import picks up new keys.
3. **`tests/server/test_wrong_retry.py`** - formula / stamp fields / same-verb retry / p50 / empty target.
4. **This claim**.

## Evidence (path:lines)

- Stamp module: `agent_coord/server/wake_first.py` (`KPI_WRONG_N`, `KPI_RETRY`, `note_rpc`)
- RPC hooks: unchanged from A1 (`api/mill/rpc.py` `note_rpc` ok/fail)
- Scrape + book: `agent_coord/server/score_tick.py` (`measure_wrong_retry`, `BOOK_PERF` opt-in)
- Tests: `tests/server/test_wrong_retry.py`

## Glance (host / Operator)

1. Opt in: `mill score-add mill-office.wrong_verb_n` and `mill score-add mill-office.retry_before_ok`.
2. Run `mill score-tick --once` (or wait mill-score 900s) after desks have stamped `wake.first_ok` with `wrong=` / `retry=`.
3. Floor `/api/floor?parts=scores` (or SCORE v1) shows Last = p50 wrong / p50 retry; target blank.
4. Confirm no new Wall chrome and no Server-Timing on floor/v1 hot path.

## Open edges (flagged)

- **Unknown verb before handler:** `dispatch` raises `unknown mill verb` before `note_rpc`; those replies are not counted (same as A1). Handler exceptions and day-one fails are counted.
- **SoR subset:** stamp is in-process (mill-wall process). Restart clears un-stamped sessions; already-emitted mill-perf lines remain for scrape.
- **Multi-worker:** each mill-wall process has its own session map (same as Hub rooms).
- **A1 fields unchanged:** `ms=` / `rpc=` scrape still works; A2 only adds `wrong=` / `retry=`.
- Wall chip label for these KPIs = follow-on; out of A2.

## Out of scope

- Shot A6 (do not start)
- Wall UI chip / Loop-3 paint
- Push / pack / PyPI / Playwright / mill-wall recycle
- Server-Timing or floor `?timings=` always-on
- New activity/event SoR table
- Counting unknown verbs outside WALL before bearer resolve

## Ready for Validator

Local commit + pytest green on formula tests. Operator opts in via score-add; no Wall change required to measure.
