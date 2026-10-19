# Claim - A5 agent value: hold-blocked hours

Status: **local WIP** on `claim/floor-v1-parts`. Committed locally only. Not pushed. Not pack/PyPI.

Parent tip: A6 verbs-to-done stamp + book KPI (`a015648`). Product **activity** Shot A5 (Operator GO after A6). No new Wall chrome. No always-on Server-Timing. No hot-path tax on `/api/floor` or `/api/v1`.

Related: cloud-mill todo **#56** (HINT TODO wake path observed on mill-perf `hint=TODO id=56`) - mutex wait pairs with wake friction (A1/A2) and card depth (A6); hold-blocked is agent time stuck behind RES_* holds.

## Roles only

No personal identifiers in commits, Claims, or docs - roles only (host, desk, human, agent, ROLE_Admin, PROJ_Office).

## Lock

Measure **how much agent time is stuck behind mill holds** (mutex deny -> later acquire). Prefer existing mill-perf + score_tick book path (opt-in `mill score-add` like `mill-office.verbs_to_done`). Smallest wire: in-process per-(desk, resource) wait on hold `ok=False` -> one `op=hold.blocked` mill-perf line when the same desk later acquires (`ok=True`); score_tick **sums** `ms=` into opt-in book KPI.

Book publishes int Last (same as A1/A2/A6). Unit in the name is **ms** (sum of wait ms in window). Product "hours" = Last / 3_600_000 for glance; Wall chip label = follow-on.

## Formula

| Field | Value |
| --- | --- |
| Start | Successful mill `hold` handler returns **`ok=False`** (RES_* held by another desk). First deny for (desk, resource) starts `t0`; later denials keep `t0` |
| End | Same desk `hold` returns **`ok=True`** on that resource (acquired / refreshed own hold) |
| Duration | `(t_acquire - t0)` wall ms on the stamp line `ms=` |
| Stamp | One per wait episode: `op=hold.blocked ms=... desk=DESK_* resource=RES_* holder=DESK_* ok=1` |
| Clear without stamp | Process restart; waiter never re-acquires (open edge) |
| KPI | `mill-office.hold_blocked_ms` = **sum** of `ms=` on those lines in `WINDOW_S=3600` |
| Target | `""` (informational; no red alarm) |
| Owner / roster | `ROLE_Admin` / `PROJ_Office` |
| Cadence | score_tick every `EVERY_S=900` |
| Opt-in | `mill score-add mill-office.hold_blocked_ms` |

## Allowed files / diff

1. `agent_coord/server/hold_blocked.py` (new) - wait sessions; emit `hold.blocked`; BOOK_PERF KPI
2. `agent_coord/server/api/mill/rpc.py` - `note_hold` after dispatch + dispatch_ws (handler returned; includes hold `ok=False`)
3. `agent_coord/server/score_tick.py` - merge BOOK_PERF; `measure_hold_blocked` sum; measure() publishes opt-in
4. `tests/server/test_hold_blocked.py` - formula / deny-then-acquire / no-wait acquire / p-sum / empty target
5. `docs/claims/CLAIM-agent-value-a5-hold-blocked.md` (this claim)

## Acceptance

1. Pytest green on `tests/server/test_hold_blocked.py`
2. KPI name `mill-office.hold_blocked_ms` in BOOK_PERF; BOOK_TARGET empty string
3. Deny (`ok=False`) then acquire (`ok=True`) emits exactly one `op=hold.blocked` with `ms=` >= 0
4. Acquire with no prior deny emits nothing
5. `measure_hold_blocked` returns **sum** of in-window `ms=` (not p50)
6. No Wall chrome / pack / PyPI / always-on Server-Timing / floor hot-path tax
7. Local commit only (no push); roles only in claim + commit message
8. Note aws #56 in claim

## What landed

1. **gent_coord/server/hold_blocked.py** - wait sessions on hold ok=False; emit hold.blocked on later ok=True; BOOK_PERF KPI.
2. **gent_coord/server/api/mill/rpc.py** - note_hold after dispatch + dispatch_ws (handler returned).
3. **gent_coord/server/score_tick.py** - merge BOOK_PERF; measure_hold_blocked sum; measure() publishes opt-in.
4. **	ests/server/test_hold_blocked.py** - formula / deny-then-acquire / no-wait / keep-t0 / sum / empty target.
5. **This claim**.

## Evidence (path:lines)

- Stamp module: gent_coord/server/hold_blocked.py
- RPC hooks: gent_coord/server/api/mill/rpc.py (dispatch, dispatch_ws)
- Scrape + book: gent_coord/server/score_tick.py (measure_hold_blocked, BOOK_PERF opt-in)
- Tests: 	ests/server/test_hold_blocked.py

## Glance (host / Operator)

1. Opt in: `mill score-add mill-office.hold_blocked_ms` (checkout PYTHONPATH if PATH mill lacks BOOK_PERF name).
2. Run `mill score-tick --once` (or wait mill-score 900s) after desks have stamped `hold.blocked` in mill-perf.
3. Floor `/api/floor?parts=scores` (or SCORE v1) shows Last = sum wait ms in last hour; target blank; hours = Last/3600000.
4. Confirm no new Wall chrome and no Server-Timing on floor/v1 hot path.

## Open edges (flagged)

- **SoR subset:** stamp is in-process (mill-wall process). Restart clears open waits; already-emitted mill-perf lines remain for scrape.
- **Multi-worker:** each mill-wall process has its own wait map (same as Hub / wake_first / verbs_to_done).
- **Holder drop without waiter retry:** wait session stays until acquire or restart (no fan-out on drop).
- **Int hours:** book Last is ms sum (int-safe). `_h` would truncate under existing `str(int(...))` publish.
- Wall chip label for this KPI = follow-on; out of A5.

## Out of scope

- Shot A3 / A4 (do not start)
- Wall UI chip / Loop-3 paint
- Push / pack / PyPI / Playwright / mill-wall recycle
- Server-Timing or floor `?timings=` always-on
- New activity/event SoR table
- Changing hold upsert SQL / HoldHeld raise path

## Ready for Validator

Local commit + pytest green on formula tests. Operator opts in via score-add; no Wall change required to measure.
