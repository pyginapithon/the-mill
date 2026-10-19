# Claim - migrate.ensure refreshes sp_name / sp_member / sp_join

Status: **Landed** on `claim/ensure-sp-join-member-name` (on main 0.6.14 `0c26acc`). Not PyPI. No pack.

## Gap

`migrate.ensure` on an existing book refreshed every `mill_watcher_*` from
`sp_activity.sql` (tip `p_type ENUM('todo','join','hold','score')`), but from
`sp_join.sql` only `mill_join_reset`, from `sp_name.sql` only `mill_name_reclaim`,
and nothing from `sp_member.sql`. A book that only runs ensure kept the old
`mill_join_upsert` / `mill_member_put` / `mill_member_delete`, which still
`CALL mill_watcher_put('name', ...)` / `mill_watcher_delete('name', ...)`
(removed in `f2a1e47`). Seat mint then failed with 1265 (data truncated on the ENUM).

## Fix

| Change | Where |
|--------|-------|
| `_SP_FULL_REFRESH = ("sp_name.sql", "sp_member.sql", "sp_join.sql")`; `_ensure_sp_full` re-applies every `DROP/CREATE PROCEDURE` in those files via `split_script` + `_apply_stmt` | `agent_coord/install/migrate.py` |
| `ensure` runs `_ensure_sp_full` right after `_ensure_watcher_hint` (callees at tip first) | `agent_coord/install/migrate.py` |

Not added: `wipe.sql`, `tables.sql`, `name_type.sql` (data shape, run by hand).
`sp_todo.sql` / `sp_hold.sql` call `mill_watcher_put` only with `'todo'` / `'hold'`, still in the ENUM.
`sp_mail.sql` was already fully refreshed by `_ensure_mail_sp` (covers `mill_mail_get`).

## Test

`tests/server/records/test_ensure_sp_refresh.py` (`-m sql`): plants old-shape callers,
proves the stale `mill_join_upsert` raises 1265 against tip `mill_watcher_put`, then
`ensure` must leave no `'name'` watcher call and `mill_join_upsert` calling
`mill_watcher_put('join', ...)`; every procedure in the three files is re-created; idempotent.
Old `migrate.py`: 2 failed. New: 4 passed.
