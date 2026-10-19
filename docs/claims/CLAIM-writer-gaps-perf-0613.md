# Claim - 0.6.13 writer gaps + perf punch

Status: **Landed** on `claim/floor-v1-parts` (on main 0.6.12). Local commit only. Not pushed. Not PyPI. No pack.
Parent: source-docs mail **408-421** (writer gaps) + human perf punch.

**Superseded in part** by `CLAIM-reconsidered-writers-fk-0613.md` (same branch): mail id is `mail.id` AUTO_INCREMENT again (no invented id), delete SPs take the card off every plan themselves, FK RESTRICT pass. Rows below marked (superseded) no longer hold.

## Locks kept (soft-delete GOs)

| Lock | Honored |
|------|---------|
| Soft-delete never rewrites `activity.desk_id`; no `mill_activity_put` on delete | Yes (todo/mail/score delete stamp only) |
| Tree prune stays with the caller; delete while still in a tree is refused (trigger / score SP SIGNAL) | (superseded) Delete SPs now run `mill_tree_detach` (one `mill_tree_remove` per plan). Triggers still refuse a direct DELETE |
| Perf item 2 (`SELECT tr.name_id, n.name ... JOIN name` cursor) | (superseded) `mill_tree_detach` loops `MIN(name_id)` on `tree` alone; no JOIN name |

## Writer gaps landed

| # | Fix | Where |
|---|-----|-------|
| 1 | `mill_mail_insert`: roster is a project, else a role (`MILL_NAME_GET` project then role); (superseded: letter first, then activity, FKs off only around that pair). Broadcast (`''`/`*`/self) goes to that project or role | `sp_mail.sql` |
| 1a | (superseded, removed) The invented letter id is gone. `mail.id` AUTO_INCREMENT allocates; see the reconsidered claim | `sp_mail.sql`, `docs/requirements/activity.md` |
| 1b | `mill_mail_to_put` no longer mints a `project` named after `p_group` (the value was unused; a role roster would have minted a junk project) | `sp_mail.sql` |
| 2 | `mill_join_reset` / `mill_hold_delete` pass NULL roster to `mill_activity_put` (row keeps its roster; not 1/Office) | `sp_join.sql`, `sp_hold.sql` |
| 3 | `mill_name_reclaim` blocks only a live seat: token set AND (desk_id = name OR desk is a member of the name). Old precedence blocked any seat row of that desk even with a NULL token | `sp_name.sql` |
| 5 | `mill_score_delete(p_id, p_desk)`; card kept; desk is caller context only | `sp_score.sql` |
| 6 | `mill_todo_delete` / `mill_mail_delete` already take the desk; still no desk_id rewrite, no activity_put | verified |
| 4 | Other summary items already law (soft-delete stamp, watcher clear, tree gate) | verified, untouched |

Python: `records/name.roster_name` (bare PROJECT then ROLE) used by mail insert + `list_project`, todo select, score select. `todo.delete` / `score.delete` require desk (`CoordError` when empty); `score.delete(id, desk)` matches the 2-arg SP.

## Perf punch landed (1, 3, 4)

| # | Change | Where |
|---|--------|-------|
| 1 | `mill_mail_list`: newest 500 letters first (derived table), then one row per letter with every dest in `dests` (`JSON_ARRAYAGG ... GROUP BY`). `mill_floor_part` mail: in-scope letter ids into temp `mill_floor_mail` (sender and dest legs, each one indexed JOIN), newest 500, one row per letter with `dests`. Floor Python reads `dests` instead of a second `tos_by_id` read. `group_list_rows` reads both shapes | `sp_mail.sql`, `sp_floor_scope.sql`, `records/mail.py`, `records/floor.py` |
| 3 | `mill_floor_part` agents/todos/holds/scores/events JOIN `mill_floor_desk` (no `IN (SELECT ...)` / `EXISTS`); one temp-table reference per statement | `sp_floor_scope.sql` |
| 4 | Floor mailbox/todos/scores resolve roster ids once (`name.roster_ids`, project before role, retired/unknown skipped, never minted) then one `IN (...)` read (`mail.list_rosters` keeps newest 500 per roster via ROW_NUMBER; `todo.select_rosters`; `score.select_rosters`). Empty ids -> `[]`. An empty name keeps the old all-letters read | `records/name.py`, `mail.py`, `todo.py`, `score.py`, `floor.py` |

Shape notes: the 500 cap is now 500 letters (was 500 letter x dest rows). Floor mail SP rows drop the per-dest `dst` / `dst_type` columns (Python never read them). Wire JSON out of floor/v1 is unchanged.

`migrate.ensure` refreshes `mill_mail_*`, `mill_hold_delete`, `mill_name_reclaim`, `mill_floor_part`, `mill_score_delete` on an existing book.

## Prove

- Throwaway A/B (HOST.md): (A) `apply_records`, (B) `mysql` whole-file per `apply_order.txt`, (C) origin/main SQL then `migrate.ensure`. All routines present; read paths do not mint names; `mill_score_delete` has 2 params; `mill_mail_insert` had no FK toggle at this tip (superseded). **PASS** (A/B/C).
- New tests: `tests/server/records/test_writer_gaps.py`, `tests/server/records/test_perf_punch.py`, plus a JSON-dests case in `tests/server/test_cold_sql_mailbox_fp.py`.
- Full regression on the claim worktree, isolated DBs (`tests/sql_isolate.py`): `pytest tests -m "not sql"` 1274 passed, 8 skipped; `pytest tests -m sql` 172 passed. Green.

## Surface

No pack / PyPI / push. No live book SQL apply.

## Tip

Code commit at land: `77248b1` on `claim/floor-v1-parts`.
