# Claim - soft-delete stack #95 / #96 / #97 + FK punch eval

Status: **Landed** on `claim/floor-v1-parts` (#95, #96, #97 + the two agreed FK lines). Local commit only. Not pushed. Not PyPI.
**No pack / live book apply** until throwaway A/B PASS reported (A/B/C PASS below; standing apply after).
FK punch beyond the two agreed lines: **evaluated, not landed** (no grok-tui eval yet; human rule: both agree or stop and discuss).

Parent: soft-delete-activity #89 (source-docs mail **351**, root **204**).

| Todo | need_id | Builder punch | grok-tui GO |
|------|---------|---------------|-------------|
| 95 | soft-delete-score-keep | mail **381** | mail **384** |
| 96 | join-desk-restrict-no-delete | mail **382** | mail **388** |
| 97 | soft-delete-labels-hold-watcher | mail **385** | mail **389** |

## Lock (Builder + grok-tui agree)

| # | Line | Honored |
|---|------|---------|
| 95 | `fk_score_evidence_score` ON DELETE RESTRICT (tables.sql + migrate drop/re-add) | Yes |
| 95 | `mill_score_delete`: no DELETE score, no DELETE score_evidence; stamp activity deleted+updated only | Yes |
| 95 | No mill_activity_put; no desk_id / roster_id write (mail 353 leave desk_id still stands) | Yes |
| 95 | 30-day day-row prune + 1970 hour rows untouched | Yes (sp_score evidence path not edited) |
| 95 | `fk_score_activity` stays CASCADE | Yes |
| 95 | Stamp no longer gated on DELETE ROW_COUNT (gated on card exists; first stamp kept on re-delete) | Yes |
| 96 | `fk_join_desk` ON DELETE RESTRICT (tables.sql + migrate drop/re-add) | Yes (see FK finding F1) |
| 96 | `fk_join_activity` stays CASCADE | Yes |
| 96 | `mill_join_reset`: NULL token_hash + stamp time_disconnect; no DELETE join/activity | Yes |
| 96 | `mill_join_socket` close path left alone | Yes |
| 96 | `join_no_delete_in_tree` stays (SIGNAL only when tree cites) | Yes |
| 96 | `prune_dead` delete retired (null token = disconnect history) | Yes (counts only; `pruned` always 0, adds `dead`, `note`) |
| 96 | Seat delete path: none exists today; any future one must mill_tree_remove first | Noted (no code) |
| 97 | Labels stay on kept activity (no label delete on soft-delete) | Yes |
| 97 | hold BEFORE DELETE always SIGNAL (`hold_no_delete`, replaces `hold_no_delete_in_tree`) | Yes |
| 97 | `mill_hold_delete` stays UPDATE desk_id=NULL + mill_activity_put; no deleted stamp | Yes (untouched) |
| 97 | Todo/score: keep tree gate, no mill_tree_remove inside the proc | Yes (todo: trigger; score: proc SIGNAL) |
| 97 | After the gate: DELETE watcher (type,id), then stamp; same transaction | Yes (refusal rolls back watcher delete - tested) |
| 97 | `activity_del_watchers` backstop only; mail/hold get no watcher delete | Yes |

## Files

- `agent_coord/server/sql/tables.sql` - two FK rules; `hold_no_delete` trigger
- `agent_coord/server/sql/wipe.sql` - drop `hold_no_delete`
- `agent_coord/server/sql/sp_score.sql` - `mill_score_delete` keep card + tree gate + watcher clear
- `agent_coord/server/sql/sp_todo.sql` - `mill_todo_delete` watcher clear before stamp
- `agent_coord/server/sql/sp_join.sql` - `mill_join_reset` stamps time_disconnect
- `agent_coord/server/records/join.py` - `prune_dead` deletes nothing
- `agent_coord/__main__.py`, `agent_coord/server/api/mill/rpc.py` - reset / --dead copy
- `agent_coord/install/migrate.py` - ensure: hold trigger swap, `mill_join_reset`, `_ensure_fk_rules` (idempotent FK flip)
- `tests/server/records/test_soft_delete_stack.py` - new
- `test_records.py`, `test_activity_lifecycle.py`, `test_soft_delete_activity_state.py`, `test_join_prune_dead.py` - updated for score keep / hold trigger / prune_dead
- `docs/requirements/activity.md`, `docs/protocol/verbs.md`, `docs/protocol/records.md`

## Blast radius (Python + SP callers)

| Change | Callers checked | Break risk | Action |
|--------|-----------------|------------|--------|
| score delete keeps card | `records/score.delete`; tests `test_records`, `test_activity_lifecycle`, `test_soft_delete_activity_state`, `test_roster_sp_punch` | 2 tests asserted the score row was gone | tests updated |
| score delete keeps card | readers: `mill_score_select`, `mill_floor_scope` scores part + fp, `glance.py` live-score count / office scores, `mill_join_select` recent_activity | soft-deleted KPI still listed on wall/floor/glance | **not fixed** (grok-tui 384: surface not this punch) - follow-on |
| score delete keeps card | `mill_score_upsert` (UNIQUE roster,desk,kpi), `mill_score_event` / `mill_wall_event` | soft-deleted score on upsert **revives** (clear `activity.deleted` inside `mill_score_upsert` only; never `mill_activity_put`); evidence kept | **landed** F2 (human GO 2026-10-05 + grok-tui) |
| evidence RESTRICT | DELETE score: only old mill_score_delete (gone); DELETE activity: only `prune_dead` (join rows; retired) | none in product code | - |
| join RESTRICT | DELETE name: no code path (retire/reclaim/mill_name_delete stamp `name.deleted`) | none | - |
| reset stamps time_disconnect | `rpc._h_reset`, `records/join.reset`, Wall presence reads | desk shows disconnected after reset (token is cleared anyway) | intended (GO 388) |
| prune_dead no delete | `rpc._h_reset --dead`, CLI `mill reset --dead`; no consumer of `pruned` found | shape change (`pruned`=0, `dead`, `note`) | tests updated |
| hold always SIGNAL | DELETE hold: none in code; release = UPDATE | none | - |
| watcher clear | `mill_todo_delete`, `mill_score_delete` | none (watchers were orphaned before) | - |
| door tables | `admin/door.py` deletes legacy `agent_human*` / `agent_grant` / `agent_vouch` (not in tables.sql, no FK) | none | - |

## FK punch - per-line eval (validated vs code paths; not rubber-stamped)

**Update (0.6.13 reconsidered punch):** every mill FK to `name` is now RESTRICT, payload FKs to activity are RESTRICT, and `name_no_delete` refuses a hard name delete. `fk_label_activity` and `fk_mail_to_mail` stay CASCADE. `fk_human_desk_desk` / `fk_human_member_name` are parked for the human-table redo. See `CLAIM-reconsidered-writers-fk-0613.md`. The table below is the earlier evaluation.

Code-path facts: no product code deletes a `name`, `human`, or `mill_invite` row (retire/reclaim and `mill_name_delete` stamp/unstamp `name.deleted`; invites revoke by stamp). After #96 no product code deletes an `activity` row. So most rules only bite a manual purge - but InnoDB cascades skip triggers, so a CASCADE path silently bypasses `hold_no_delete` and the `*_no_delete_in_tree` guards.

| FK | Today | Verdict | Status | Why |
|----|-------|---------|--------|-----|
| fk_score_evidence_score | CASCADE | ACCEPT RESTRICT | **landed** (agreed 381/384) | proved: DELETE score and DELETE activity(score) refused while evidence exists |
| fk_join_desk | CASCADE | ACCEPT RESTRICT | **landed** (agreed 382/388) | ineffective alone - see F1 |
| fk_join_activity | CASCADE | KEEP | agreed keep | grok-tui 388 |
| fk_score_activity | CASCADE | KEEP | agreed keep | grok-tui 384 |
| fk_label_activity | CASCADE | KEEP | agreed keep | soft-delete keeps activity so labels stay (389) |
| fk_mail_to_mail | CASCADE | KEEP | agreed keep | `mill_mail_delete` relies on it (#94 lock) |
| fk_activity_desk | CASCADE | ACCEPT RESTRICT | **landed** (human GO 2026-10-05 + grok-tui) | F1: DELETE name with seat refused (1451); fk_join_desk RESTRICT is real. tables.sql + migrate _FK_RULES. No code deletes names |
| fk_todo_creator / fk_todo_updated | CASCADE | ACCEPT RESTRICT (proposed) | not landed | name purge would drop cards; history |
| fk_mail_desk | CASCADE | ACCEPT RESTRICT (proposed) | not landed | sender purge drops letters |
| fk_score_desk | CASCADE | ACCEPT RESTRICT (proposed) | not landed | already blocked when evidence exists; make it uniform |
| fk_hold_desk | CASCADE | ACCEPT SET NULL (proposed) | not landed | NULL desk_id = released; CASCADE bypasses `hold_no_delete` |
| fk_hold_res | CASCADE | ACCEPT RESTRICT (proposed) | not landed | res purge would delete holds, bypassing `hold_no_delete` |
| fk_mail_to_desk | CASCADE | LEAN ACCEPT RESTRICT - discuss | not landed | recipient/receipt history vs. a link row |
| fk_member_name / fk_member_desk | CASCADE | REJECT change (keep) | - | membership is a link; `mill_member_delete` deletes directly; no effect on retire/reclaim |
| fk_label_name | CASCADE | REJECT change (keep) | - | tag link |
| fk_watcher_desk | CASCADE | REJECT change (keep) | - | subscription link; soft-delete clears watchers explicitly now |
| fk_push_queue_desk | CASCADE | REJECT change (keep) | - | transient queue (30-day delete in `mill_push_take`) |
| fk_human_desk_human / fk_human_member_human | CASCADE | REJECT change (keep) | - | human door: a future human revoke must drop its bindings; RESTRICT would break it |
| fk_human_desk_desk / fk_human_member_name | CASCADE | REJECT change (keep) | - | door binding links; `sp_human` refresh deletes `human_member` by human_id directly |
| fk_invite_join_key | CASCADE | REJECT change (keep) | - | invite rows revoke by stamp; link rows |
| fk_activity_roster | RESTRICT | KEEP | - | already RESTRICT |
| fk_mail/todo/score_roster, fk_todo_assigned | SET NULL | KEEP | - | nullable; roster punch keeps cols |
| fk_tree_name / fk_tree_activity | NO ACTION | KEEP | - | this is what refuses activity delete while in a tree |
| fk_mail_activity / fk_todo_activity / fk_hold_activity | CASCADE | KEEP (superseded: all five payload-to-activity FKs dropped in #216) | - | no product activity delete after #96; `test_deleting_activity_removes_the_live_detail` relies on it |

## Findings to discuss

- **F1** **landed**: `fk_activity_desk` ON DELETE RESTRICT (tables.sql + migrate). `test_name_delete_with_seat_refused` now passes (was strict-xfail).
- **F2** **landed**: `mill_score_upsert` clears `activity.deleted` (and bumps `updated`) when the kept card is re-reported. Never in `mill_activity_put`. Evidence kept.
- **F3** Surfaces still list soft-deleted scores (see blast radius). Follow-on like #91-93.
- **F4** Pre-existing, unrelated: `mill_tree_create` / attach call `mill_activity_put(type, id, ts, 1, 1, ...)`, rewriting the card's activity `desk_id` to 1 (Office project id, not a desk). Seen in A/B.
- **F5** Pre-existing test failure: `tests/wall/test_wall_surface.py::test_html_validate_board` fails at base e3978d7 too.

## Prove

- Throwaway A/B/C: `python tmp/ab_soft_delete_stack_prove.py` - A apply_records, B mysql whole-file, C base e3978d7 book + `migrate.ensure` (flips FKs incl. fk_activity_desk, swaps hold trigger; proves F1 name-delete refuse + F2 score revive). **A/B/C PASS** (see tip).
- pytest `tests/server/records/test_soft_delete_stack.py` covers F1/F2 (no xfail).

## Tip

Code `847abaf` on `claim/floor-v1-parts` (F1+F2; prior stack `7437fa0` / docs tip `7cbcc8d`). A/B/C PASS at `847abaf`.

## Surface

No pack / PyPI / push / force-push. No live aws/lan book SQL apply. Mill land note in source-docs.
