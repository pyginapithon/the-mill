# Claim - A3 agent value: Nest SoR hit + re-ask

Status: **local WIP** on `claim/floor-v1-parts`. Committed locally only. Not pushed. Not pack/PyPI.

Parent tip: A5 hold-blocked stamp + book KPI (`4feff61`). Product **activity** Shot A3 (Operator GO after A5). No new Wall chrome. No always-on Server-Timing. No hot-path tax on `/api/floor` or `/api/v1`.

Related: cloud-mill todo **#56** (`agent-value-kpi-a1-a6`) SoR line: **A3 todos SoR Nest hit + re-ask same todo_id**. Nest = TODO Board|List|Nest (TREE-backed todo); sibling A4 is MAIL Threads.

## Roles only

No personal identifiers in commits, Claims, or docs - roles only (host, desk, human, agent, ROLE_Admin, PROJ_Office).

## Lock

Measure **Nest SoR reads** and **re-asks of the same todo id** (agent did not retain Nest context). Prefer mill-perf + score_tick book path (opt-in `mill score-add`). Smallest wire: mill `todo` peek of one need whose card is **on a TREE** -> one `op=nest.hit` mill-perf line per peek; `reask=0` first time for that desk+todo in-process, `reask=1` on later peeks. score_tick **counts** hits / reasks in `WINDOW_S=3600`.

Not Wall Nest paint. Not `/api/v1/todos` poll. Not board-wide `todo` list without a need.

## Formula

| Field | Value |
| --- | --- |
| Nest hit | Successful mill `todo` with a **need** filter returning **one** card that `tree.on_tree("todo", id)` |
| First vs re-ask | In-process per (desk, todo_id): first hit `reask=0`; later hits `reask=1` |
| Stamp | `op=nest.hit ms=0 todo=ID need=... desk=DESK_* reask=0|1 ok=1` |
| KPI hit | `mill-office.nest_hit_n` = **count** of `nest.hit` lines in `WINDOW_S=3600` |
| KPI reask | `mill-office.nest_reask_n` = **count** of those lines with `reask=1` |
| Target | `""` (informational; no red alarm) |
| Owner / roster | `ROLE_Admin` / `PROJ_Office` |
| Cadence | score_tick every `EVERY_S=900` |
| Opt-in | `mill score-add mill-office.nest_hit_n` and/or `mill score-add mill-office.nest_reask_n` |

## Allowed files / diff

1. `agent_coord/server/nest_sor.py` (new) - hit sessions; emit `nest.hit`; BOOK_PERF KPIs
2. `agent_coord/server/api/mill/rpc.py` - mark `nest=1` on single-need todo peek when on_tree; `note_nest` after dispatch + dispatch_ws
3. `agent_coord/server/score_tick.py` - merge BOOK_PERF; `measure_nest_sor` counts; measure() publishes opt-in
4. `tests/server/test_nest_sor.py` - formula / first vs reask / non-nest / board list skip / counts / empty target
5. `docs/claims/CLAIM-agent-value-a3-nest-sor.md` (this claim)

## Acceptance

1. Pytest green on `tests/server/test_nest_sor.py`
2. Both KPI names in BOOK_PERF; BOOK_TARGET empty string
3. Nest-backed single peek stamps `reask=0` then later `reask=1`
4. Non-nest card or board list (no need) emits nothing
5. `measure_nest_sor` returns (hit_count, reask_count) over WINDOW_S
6. No Wall chrome / pack / PyPI / always-on Server-Timing / floor hot-path tax
7. Local commit only (no push); roles only; note aws #56

## What landed

1. **`agent_coord/server/nest_sor.py`** - hit memory; emit `nest.hit` with reask=; BOOK_PERF KPIs.
2. **`agent_coord/server/api/mill/rpc.py`** - `_h_todo` marks `nest=1` on single-need TREE peek; `note_nest` after dispatch + dispatch_ws.
3. **`agent_coord/server/score_tick.py`** - merge BOOK_PERF; `measure_nest_sor` counts; measure() publishes opt-in.
4. **`tests/server/test_nest_sor.py`** - formula / first vs reask / non-nest / board skip / counts / empty target.
5. **This claim**.

## Evidence (path:lines)

- Stamp module: `agent_coord/server/nest_sor.py`
- Todo nest mark + RPC hooks: `agent_coord/server/api/mill/rpc.py` (`_h_todo`, `dispatch`, `dispatch_ws`)
- Scrape + book: `agent_coord/server/score_tick.py` (`measure_nest_sor`, `BOOK_PERF` opt-in)
- Tests: `tests/server/test_nest_sor.py`

## Glance (host / Operator)

1. Opt in: `mill score-add mill-office.nest_hit_n` and `mill score-add mill-office.nest_reask_n`.
2. Run `mill score-tick --once` after desks stamp `nest.hit` in mill-perf.
3. Floor scores show Last = hit count / reask count; target blank.
4. Confirm no new Wall chrome and no Server-Timing on floor/v1 hot path.

## Open edges (flagged)

- **SoR subset:** in-process hit map (mill-wall process). Restart clears prior-hit memory; mill-perf lines remain.
- **Multi-worker:** per mill-wall process map.
- **Wall Nest UI / v1 todos poll:** not stamped (no always-on Wall tax). Agents measure via mill `todo` peek.
- **Board list without need:** not a Nest hit (no todo_id ask).
- Wall chip labels = follow-on; out of A3.

## Out of scope

- Shot A4 (MAIL Threads hit + re-ask) - do not start
- Wall UI chip / Loop-3 paint
- Push / pack / PyPI / Playwright / mill-wall recycle
- Server-Timing or floor `?timings=` always-on
- New activity/event SoR table

## Ready for Validator

Local commit + pytest green on formula tests. Operator opts in via score-add; no Wall change required to measure.
