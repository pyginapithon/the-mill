# Claim - A6 agent value: verbs-to-done

Status: **local WIP** on `claim/floor-v1-parts`. Committed locally only. Not pushed. Not pack/PyPI.

Parent tip: A2 wrong-verb/retry stamp + book KPIs (`fe6da16`). Product **activity** Shot A6 (Operator GO after A2). No new Wall chrome. No always-on Server-Timing. No hot-path tax on `/api/floor` or `/api/v1`.

Related: cloud-mill todo **#56** (HINT TODO wake path observed on mill-perf `hint=TODO id=56`) - card lifecycle measure pairs with wake friction (A1/A2); verbs-to-done is claim->done depth on a card.

## Roles only

No personal identifiers in commits, Claims, or docs - roles only (host, desk, human, agent, ROLE_Admin, PROJ_Office).

## Lock

Measure **count of mill verbs on a card from claim to done** (pass reaches `done`). Prefer existing mill-perf + score_tick book path (opt-in `mill score-add` like `mill-office.wake_first_*`). **Exclude note spam**: `note` verbs stamp as `notes=` only, not in `verbs=`. Smallest wire: in-process per-card session on claim/assign -> one `op=card.verbs_to_done` mill-perf line at done; score_tick scrapes p50 into agent_kpi book.

## Formula

| Field | Value |
| --- | --- |
| Start | Successful `claim` or `assign` on a todo (resets window); counts as `verbs=1` |
| End | Successful `pass` that lands status **`done`** (claimed->shipped keeps counting; does not stamp) |
| verbs | Count of **ok** card verbs in window **excluding** `note`: claim/assign + pass(shipped) + pass(done) + unclaim-not-reached |
| notes | Count of ok `note` verbs in window (stamped; **not** in KPI) |
| unclaim | Clears window **without** stamp (abandoned claim) |
| Stamp | One per completed card: `op=card.verbs_to_done ms=... verbs=... notes=... card=ID need=... desk=DESK_* ok=1` |
| KPI | `mill-office.verbs_to_done` = **p50** of `verbs=` on those lines in `WINDOW_S=3600` |
| Target | `""` (informational; no red alarm) |
| Owner / roster | `ROLE_Admin` / `PROJ_Office` |
| Cadence | score_tick every `EVERY_S=900` |
| Opt-in | `mill score-add mill-office.verbs_to_done` |

## What landed

1. **`agent_coord/server/verbs_to_done.py`** - CARD_VERBS; note_card; emit `card.verbs_to_done`; BOOK_PERF KPI.
2. **`agent_coord/server/api/mill/rpc.py`** - note_card after dispatch + dispatch_ws ok.
3. **`agent_coord/server/score_tick.py`** - merge BOOK_PERF; `measure_verbs_to_done` p50; measure() publishes opt-in.
4. **`tests/server/test_verbs_to_done.py`** - formula / note-exclude / unclaim / assign / p50 / empty target.
5. **This claim**.

## Evidence (path:lines)

- Stamp module: `agent_coord/server/verbs_to_done.py`
- RPC hooks: `agent_coord/server/api/mill/rpc.py` (`dispatch`, `dispatch_ws`)
- Scrape + book: `agent_coord/server/score_tick.py` (`measure_verbs_to_done`, `BOOK_PERF` opt-in)
- Tests: `tests/server/test_verbs_to_done.py`

## Glance (host / Operator)

1. Opt in: `mill score-add mill-office.verbs_to_done`.
2. Run `mill score-tick --once` (or wait mill-score 900s) after cards have stamped `card.verbs_to_done` in mill-perf.
3. Floor `/api/floor?parts=scores` (or SCORE v1) shows Last = p50 verbs; target blank.
4. Confirm no new Wall chrome and no Server-Timing on floor/v1 hot path.

## Open edges (flagged)

- **SoR subset:** stamp is in-process (mill-wall process). Restart clears open claim windows; already-emitted mill-perf lines remain for scrape.
- **Multi-worker:** each mill-wall process has its own card session map (same as Hub rooms / wake_first).
- **Note spam:** every ok `note` increments `notes=`; KPI uses `verbs=` only. No collapse of consecutive notes beyond exclude-from-verbs.
- **Pass asker path:** shipped->done may be asker desk; stamp `desk=` is claim/assign volunteer (card owner), not the final passer.
- Wall chip label for this KPI = follow-on; out of A6.

## Out of scope

- Shot A5 (do not start)
- Wall UI chip / Loop-3 paint
- Push / pack / PyPI / Playwright / mill-wall recycle
- Server-Timing or floor `?timings=` always-on
- New activity/event SoR table
- Counting non-card verbs (send/inbox/hold) toward card depth

## Ready for Validator

Local commit + pytest green on formula tests. Operator opts in via score-add; no Wall change required to measure.
