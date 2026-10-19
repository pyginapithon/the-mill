# Claim - soft-delete activity (#89) + mill_activity_select state (#90)

Status: **Landed** on `claim/floor-v1-parts`. Local commit only. Not pushed. Not PyPI.
**No pack / live book apply** until throwaway A/B PASS reported (standing apply after).

Parent shots: source-docs mail **351** / todo **#89** (`soft-delete-activity`); mail **354** / todo **#90** (`mill-activity-select-state`).
grok-tui GO: mails **353** / **356**.

## Lock (GO)

| # | Constraint | Honored |
|---|------------|---------|
| 89 | `ALTER activity ADD deleted DATETIME(6) NULL AFTER updated` | Yes (`tables.sql` + migrate ensure) |
| 89 | `mill_todo/mail/score_delete`: read card roster as needed; DELETE card; `UPDATE activity SET deleted=v_ts, updated=v_ts` | Yes |
| 89 | Do NOT change `activity.desk_id` | Yes |
| 89 | Do NOT `mill_activity_put` on these deletes | Yes |
| 89 | Leave `name_type.sql` DELETE activity for name alone | Yes (untouched) |
| 89 | Keep roster_id columns | Yes |
| 89 | BEFORE DELETE `*_no_delete_in_tree` on todo/mail/hold/join/score (SIGNAL if still in tree; mill_tree_remove first) | Yes |
| 89 addendum | `mill_mail_delete`: before DELETE mail, `DELETE push_queue WHERE kind IN ('mail','receipt') AND CAST(JSON_UNQUOTE(JSON_EXTRACT(payload,'$.id')) AS UNSIGNED)=p_id`; mail_to cascades; UPDATE activity deleted+updated only (NO desk_id; grok-tui GO 353) | Yes |
| 90 | `mill_activity_select`: keep ANY_VALUE name cols; add state CASE | Yes |
| 90 | LEFT JOIN mail only for mail (todo separate / other types NULL) | Yes |
| 90 | Mail: deleted if `a.deleted` set, sent if `m.id` present, else NULL | Yes |
| 90 | No mail_to join | Yes |
| 90 | Do not touch `mill_activity_bucket` or `mill_span` | Yes |

## Files

- `agent_coord/server/sql/tables.sql` - `activity.deleted` + `*_no_delete_in_tree` BEFORE DELETE triggers
- `agent_coord/server/sql/wipe.sql` - drop those triggers
- `agent_coord/server/sql/sp_mail.sql` / `sp_todo.sql` / `sp_score.sql` - soft-delete stamp
- `agent_coord/server/sql/sp_activity.sql` - `mill_activity_select` state CASE
- `agent_coord/install/migrate.py` - additive ensure for live books
- `tests/server/records/test_soft_delete_activity_state.py` - new
- lifecycle + roster punch tests updated for soft-delete semantics

## Blast-radius (#91+)

Inventory mail **357** (activity-state-surface). Filed and present on the office book:

| Id | need_id | status (at land check) |
|----|---------|------------------------|
| 91 | activity-state-sp-surface | claimed |
| 92 | activity-state-wall-ui | open |
| 93 | activity-state-watcher-hint | claimed |

grok-tui GO on SP surface: mail **359**. This land (#89+#90) does not implement 91-93.

## Prove

- Throwaway A/B: `python tmp/ab_soft_delete_prove.py` (apply_records path + mysql whole-file). Soft-delete stamp + select state + push_queue mail/receipt cleanup. **PASS** (see tip note).
- pytest soft-delete/state + lifecycle + roster punch.

## Tip

Tip at land: `00f1b96` on `claim/floor-v1-parts` (no_delete_in_tree).
**mail-delete-addendum** (source-docs mail **371** / todo **#94**): tip `91a1107` on `claim/floor-v1-parts`. push_queue cleanup in `mill_mail_delete`; desk_id leave locked (grok-tui GO **353**). A/B PASS (routines 76, triggers 5; push_queue cleanup).

## Surface

No pack / PyPI / force-push. No live aws/lan book SQL apply this turn.

