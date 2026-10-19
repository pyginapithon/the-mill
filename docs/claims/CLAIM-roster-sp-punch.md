# Claim - roster SP punch (mail 308 / todos 82-88)

Status: **Locked / landed** on `claim/floor-v1-parts`. Local commit only. Not pushed. Not PyPI. **No live aws/lan book apply** until throwaway A/B reported (done below).

Parent shot: source-docs mail **308** (room `source-docs`, root 204). Parent todo **81**. SLA cards **82-88**. grok-tui + Builder ACCEPT all 7.

## Lock / hard constraints

| Constraint | Honored |
|------------|---------|
| Keep `todo.roster_id`, `mail.roster_id`, `score.roster_id` | Yes |
| Do not join activity to list cards | Yes (`mill_mail_list`, floor mail part) |
| Inserts that write both stay | Yes (mail insert writes letter + `mill_activity_put`) |
| Hold unchanged | Yes |

## Landed SP1-7

| # | Fix | Where |
|---|-----|-------|
| 1 | `mill_mail_insert` writes `v_proj` onto `mail.roster_id` | `sp_mail.sql` |
| 2 | `mill_mail_update` / `mill_mail_delete` read roster from `mail` card | `sp_mail.sql` |
| 3 | `mill_mail_list` filter/display on `m.roster_id` only; drop activity join and OR desk=proj | `sp_mail.sql` |
| 4 | `mill_todo_delete` / `mill_score_delete` read roster from todo/score card before DELETE | `sp_todo.sql`, `sp_score.sql` |
| 5 | `mill_floor_fp` project mail: `m.roster_id=v_proj` only | `sp_floor_scope.sql` |
| 6 | `mill_floor_part` mail: letter-only roster; drop activity join | `sp_floor_scope.sql` |
| 7 | Role filter: `MILL_NAME_GET('project')` then `MILL_NAME_GET('role')` on `mail_list`, `todo_select`, `score_select`, `floor_fp` | those SPs |

## Prove

- Throwaway A/B (HOST.md): `apply_records` path and `mysql` whole-file path both apply; routines present; read path does not mint junk names. **PASS**.
- `pytest tests/server/records/test_roster_sp_punch.py` + activity lifecycle SQL. **PASS**.

## Surface

No pack / PyPI / force-push. No live aws book SQL apply this turn.

## Tip

Tip at land: `14e0b6f` on `claim/floor-v1-parts`.
