# Claim - A4 agent value: MAIL Threads SoR hit + re-ask

Status: **local WIP** on `claim/floor-v1-parts`. Committed locally only. Not pushed. Not pack/PyPI.

Parent tip: A3 Nest SoR stamp + book KPIs (`b26f9ba`). Product **activity** Shot A4 (Operator GO after A3; last in A1-A6). No new Wall chrome. No always-on Server-Timing. No hot-path tax on `/api/floor` or `/api/v1`.

Related: cloud-mill todo **#56** (`agent-value-kpi-a1-a6`) SoR line: **A4 MAIL SoR Threads hit + re-ask same mail_id**. Threads = MAIL under TREE; sibling A3 is TODO Nest.

## Roles only

No personal identifiers in commits, Claims, or docs - roles only (host, desk, human, agent, ROLE_Admin, PROJ_Office).

## Lock

Measure **MAIL Threads SoR reads** and **re-asks of the same mail id** (agent did not retain thread context). Prefer mill-perf + score_tick book path (opt-in `mill score-add`). Smallest wire: mill `mail-thread` peek of one mail_id whose message is **on a TREE** -> one `op=mail.hit` mill-perf line per peek; `reask=0` first time for that desk+mail in-process, `reask=1` on later peeks. score_tick **counts** hits / reasks in `WINDOW_S=3600`.

Not Wall mailbox paint. Not `/api/v1/mailbox` poll. Not inbox list. Not deprecated mill `thread` (send alias).

## Formula

| Field | Value |
| --- | --- |
| Threads hit | Successful mill `mail-thread` with **mail_id** whose chain is TREE-backed (`thread=1` / crumbs.tree present) |
| First vs re-ask | In-process per (desk, mail_id): first hit `reask=0`; later hits `reask=1` |
| Stamp | `op=mail.hit ms=0 mail=ID desk=DESK_* reask=0|1 ok=1` |
| KPI hit | `mill-office.mail_hit_n` = **count** of `mail.hit` lines in `WINDOW_S=3600` |
| KPI reask | `mill-office.mail_reask_n` = **count** of those lines with `reask=1` |
| Target | `""` (informational; no red alarm) |
| Owner / roster | `ROLE_Admin` / `PROJ_Office` |
| Cadence | score_tick every `EVERY_S=900` |
| Opt-in | `mill score-add mill-office.mail_hit_n` and/or `mill score-add mill-office.mail_reask_n` |

## Allowed files / diff

1. `agent_coord/server/mail_sor.py` (new) - hit sessions; emit `mail.hit`; BOOK_PERF KPIs
2. `agent_coord/server/api/mill/rpc.py` - mark `thread=1` on TREE-backed mail-thread result; `note_mail` after dispatch + dispatch_ws
3. `agent_coord/server/score_tick.py` - merge BOOK_PERF; `measure_mail_sor` counts; measure() publishes opt-in
4. `tests/server/test_mail_sor.py` - formula / first vs reask / non-thread / missing id skip / counts / empty target
5. `docs/claims/CLAIM-agent-value-a4-mail-sor.md` (this claim)

## Acceptance

1. Pytest green on `tests/server/test_mail_sor.py`
2. Both KPI names in BOOK_PERF; BOOK_TARGET empty string
3. Thread-backed mail-thread stamps `reask=0` then later `reask=1`
4. Off-tree chain or missing mail_id emits nothing
5. `measure_mail_sor` returns (hit_count, reask_count) over WINDOW_S
6. No Wall chrome / pack / PyPI / always-on Server-Timing / mailbox poll stamp
7. Local commit only (no push); roles only; note aws #56

## What landed

1. **`agent_coord/server/mail_sor.py`** - hit memory; emit `mail.hit` with reask=; BOOK_PERF KPIs.
2. **`agent_coord/server/api/mill/rpc.py`** - `_h_mail_thread` marks `thread=1` when TREE crumbs present; `note_mail` after dispatch + dispatch_ws.
3. **`agent_coord/server/score_tick.py`** - merge BOOK_PERF; `measure_mail_sor` counts; measure() publishes opt-in.
4. **`tests/server/test_mail_sor.py`** - formula / first vs reask / non-thread / skip / counts / empty target.
5. **This claim**.

## Evidence (path:lines)

- Stamp module: `agent_coord/server/mail_sor.py`
- Mail-thread mark + RPC hooks: `agent_coord/server/api/mill/rpc.py` (`_h_mail_thread`, `dispatch`, `dispatch_ws`)
- Scrape + book: `agent_coord/server/score_tick.py` (`measure_mail_sor`, `BOOK_PERF` opt-in)
- Tests: `tests/server/test_mail_sor.py`

## Glance (host / Operator)

1. Opt in: `mill score-add mill-office.mail_hit_n` and `mill score-add mill-office.mail_reask_n`.
2. Run `mill score-tick --once` after desks stamp `mail.hit` in mill-perf.
3. Floor scores show Last = hit count / reask count; target blank.
4. Confirm no new Wall chrome and no Server-Timing on floor/v1 hot path.

## Open edges (flagged)

- **SoR subset:** in-process hit map (mill-wall process). Restart clears prior-hit memory; mill-perf lines remain.
- **Multi-worker:** per mill-wall process map.
- **Wall mailbox / v1 mailbox poll:** not stamped (no always-on Wall tax). Agents measure via mill `mail-thread`.
- **inbox list / off-tree single mail:** not a Threads hit.
- Wall chip labels = follow-on; out of A4.

## Out of scope

- Wall UI chip / Loop-3 paint
- Push / pack / PyPI / Playwright / mill-wall recycle
- Server-Timing or floor `?timings=` always-on
- New activity/event SoR table
- Changing lean MAIL public shape beyond additive `thread=1` on mail-thread envelope

## Ready for Validator

Local commit + pytest green on formula tests. Operator opts in via score-add; no Wall change required to measure.
