# Claim - inbox card roster + floor blank-name drop

Status: **Landed** on `claim/floor-v1-parts` (fast-forwarded onto origin/main `0639953`, 0.6.13). Local commit only. Not pushed. Not PyPI. No pack. No aws ensure.
Parent: human leftover punch, narrowed scope (consensus): card roster in the inbox read, and no per-name reads in the floor fallback.

## Claims

- **Claim 1**: "`mill_mail_select` (inbox) reports the letter's own roster: `m.roster_id` only. `IFNULL(m.roster_id, a.roster_id)` is gone from both the column and the `affn` join, and the now-unused `LEFT JOIN activity` is dropped. A letter with a NULL card roster shows NULL, so a bad insert is visible instead of being masked by the activity row." - *Evidence*: `agent_coord/server/sql/sp_mail.sql:220-245`
- **Claim 2**: "Inbox join shape unchanged: `JOIN mail_to ... WHERE t.desk_id = v_desk`, one row per (letter, this desk) - `mail_to` PK `(type, id, desk_id)` makes that one row per letter. Columns unchanged (`dst_id`, `dst`, `receipt`, ...). No dests aggregate (out of scope)." - *Evidence*: `agent_coord/server/sql/sp_mail.sql:236-244`
- **Claim 3**: "Existing books pick up the new SP through `migrate.ensure` -> `_ensure_mail_sp` (refreshes every `mill_mail_*`). No migrate change needed." - *Evidence*: `agent_coord/install/migrate.py:419-440`, `:455`
- **Claim 4**: "Floor `_mail_by_aff` / `_todo_by_aff` / `_score_by_aff` drop blank names first, then make the one IN helper read (`mail.list_rosters`, `todo.select_rosters`, `score.select_rosters`). No `list_project('')` / `todo.select(cn, '', ...)` / `score.select(cn, '')` and no read per name. All names blank or empty -> `[]`, no read. All names non-blank -> same IN path as before." - *Evidence*: `agent_coord/server/records/floor.py:1474-1500`

## Behavior note

A blank name used to switch the whole set to per-name reads, and the blank slot read every letter/card/score (no roster filter). That slot is now dropped. Floor callers build `mail_ps` from real project names (or `the-mill`), so the blank case was only the fallback.

## Tests

- `tests/server/records/test_mail.py:74-91` - `test_mail_select_card_roster_only`: card roster shown; after clearing `mail.roster_id` (activity still carries it) the inbox row has `roster_id` / `roster` / `sender_roster` NULL.
- `tests/server/records/test_perf_punch.py:144-146` - `mill_mail_select` body has no `IFNULL` and no `JOIN activity`.
- `tests/server/records/test_floor_aff_blanks.py` (new) - blanks dropped, one IN call per helper, per-name readers never called; all-blank/empty -> no read.

## Prove

- Throwaway A/B (`tmp/ab_inbox_prove.py`, not shipped): (A) `apply_records` at tip; (B) origin/main SQL via mysql CLI, live letters (one with a NULL card roster), old SP read shows the activity fallback (baseline), then `migrate.ensure` at tip. Both: inbox row per desk, receipt per desk, NULL card roster stays NULL while activity keeps it, routine body has no `IFNULL` / `JOIN activity`. **PASS** (A/B).
- Full regression on the claim worktree, isolated DBs: `pytest tests -m "not sql"` 1276 passed, 8 skipped; `pytest tests -m sql` 176 passed. Green.

## Out of scope

Dest aggregation in the inbox, human tables, nested-set, score ring, dropping the roster copy.

## Tip

Code commit at land: `9b94251` on `claim/floor-v1-parts` (parent `0639953`). Shipper held until this report.
