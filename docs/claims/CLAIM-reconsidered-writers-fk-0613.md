# Claim - 0.6.13 reconsidered writers + FK RESTRICT pass

Status: **Landed** on `claim/floor-v1-parts` (on top of the 0.6.13 writer-gaps tip). Local commit only. Not pushed. Not PyPI. No pack.
Parent: human reconsidered punch (Builder agrees). Supersedes parts of `CLAIM-writer-gaps-perf-0613.md`.

## Mail id

| Rule | Landed |
|------|--------|
| `mail.id` is the allocator: INSERT letter, `LAST_INSERT_ID()`, then `mill_activity_put`, one transaction | Yes (`sp_mail.sql`) |
| `FOREIGN_KEY_CHECKS = 0` only around the letter + activity pair (same as `mill_todo_insert`); exit handler sets it back to 1 | Yes |
| A failed activity write rolls the letter back | Yes (tested with a forced activity failure) |
| No MAX+1 id pick, no named lock, no `MILL_NEXT_ID` | Yes. The invented-id text is gone from `activity.md` and the 0.6.13 claim. `DROP FUNCTION IF EXISTS MILL_NEXT_ID` stays in `fn_name.sql` / `wipe.sql` as old-book cleanup only |

## Writers

| Writer | Landed |
|--------|--------|
| `mill_mail_insert` | roster_id: project, then role; letter then activity as above |
| `mill_mail_update` | roster from the letter (unchanged, verified) |
| `mill_mail_delete` | off every plan (`mill_tree_detach`), queued mail/receipt pushes dropped, letter deleted (`mail_to` cascades), `activity.deleted` stamped. No `mill_activity_put`; `activity.desk_id` untouched |
| `mill_todo_delete` | off every plan, watchers dropped, card deleted, stamped. Labels stay |
| `mill_score_delete(p_id, p_desk)` | score row kept; off every plan, watchers dropped, stamped |
| `mill_join_reset` | token NULL + `time_disconnect`; NULL roster to `mill_activity_put` (verified) |
| `mill_hold_delete` | `desk_id` NULL; NULL roster (verified) |
| `mill_name_reclaim` | blocked only by a live token (verified) |

Tree removal inside the delete SPs is `mill_tree_remove` semantics (children move up to the parent), not prune. New helpers in `sp_tree.sql`, no transaction of their own so they run inside the delete transaction:

- `mill_tree_detach_one(p_name, p_type, p_id)` - one node off one plan; no-op when absent. `mill_tree_remove` now calls it.
- `mill_tree_detach(p_type, p_id)` - one `mill_tree_detach_one` per plan the node sits on.

The `*_no_delete_in_tree` triggers stay and still refuse a direct DELETE of a card that is on a plan.

## Lists

- `mill_mail_list` / floor mail read `m.roster_id` (verified).
- `mill_todo_select` / `mill_score_select`: project, then role (verified).
- Floor todo cards: `need_id` is the card id (`todo.id`), not the slug from the body. `mill_floor_part` todos and the three Python card builders in `records/floor.py` (`v1_todo` too).

## Callers

`roster_name` used by mail insert / list and todo / score select. `todo.delete` / `score.delete` require a desk; tests pass one. No verb or wall route calls these deletes (checked).

## Constraints

| Rule | Landed |
|------|--------|
| Every mill FK to `name` ON DELETE RESTRICT (member, activity, label, tree, watcher, mail, mail_to, todo, join, hold, score, push_queue) | Yes |
| Payload FKs to activity (mail, todo, join, hold, score, tree) RESTRICT | Yes |
| `score_evidence` RESTRICT | Yes (kept) |
| `mail_to` CASCADE from mail | Yes (kept) |
| Watchers go only on a hard activity delete (`activity_del_watchers`) | Yes (kept) |
| BEFORE DELETE `name_no_delete` refuses a hard name delete | Yes |
| Tree guards on todo / mail / join / score; `hold_no_delete` always | Yes (kept) |
| Drop `fk_human_desk_desk` / `fk_human_member_name` | **Parked** (human): left as they are until the human-table redo |
| `fk_label_activity` | Kept CASCADE (labels go only with a hard activity delete) |

`migrate.ensure` on an existing book: `_FK_RULES` now lists every flipped key (composite `(type, id)` keys supported); `name_no_delete` added to the trigger refresh; `mill_tree_remove` / `mill_tree_detach*`, `mill_todo_select`, `mill_score_select` added to the SP refresh.

## Not in this pass

Nested-set replacement, score ring, dropping the roster copy. Queued-if-easy items (need_id / `todo.find`, rpc pack, ident, name arg, drop dead FNs) left pending.

## Prove

- Throwaway A/B/C/D (`tmp/ab_reconsidered_prove.py`, not shipped): (A) `apply_records`, (B) `mysql` whole-file per `apply_order.txt`, (C) origin/main SQL then `migrate.ensure`, (D) previous claim tip SQL then `migrate.ensure`, each with a live card before ensure. Checks every FK rule above, triggers, letter-first insert body, delete SP bodies, and behavior (ids grow past soft-deleted letters, detach moves children up, hard deletes refused). **PASS** (A/B/C/D).
- Full regression on the claim worktree, isolated DBs (`tests/sql_isolate.py`): `pytest tests -m "not sql"` 1274 passed, 8 skipped; `pytest tests -m sql` 175 passed. Green.

## Tip

Code commit at land: `52596db` on `claim/floor-v1-parts` (parent `bef46ad`). Shipper held until this report.
