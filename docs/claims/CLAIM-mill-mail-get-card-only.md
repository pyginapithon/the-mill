# Claim - mill_mail_get card-only roster (match select)

Status: **Open** on `claim/mill-mail-get-card-only` (base `d92b54e` = 0.6.15 bump, **not on PyPI**). Shipper: FF onto 0.6.15 before upload, or bump **0.6.16** if 0.6.15 already uploaded.

## Gap

`origin/main` tip `sp_mail.sql` `mill_mail_get` still has
`IFNULL(m.roster_id, a.roster_id)` plus `LEFT JOIN activity a`.
`mill_mail_select` / inbox already use card-only `m.roster_id`.
Live lan+aws books were hand-fixed to card-only; if Shipper uploads 0.6.15 and
offices run ensure, `mill_mail_get` would **rewind** the hand-fix.

## Fix

| Change | Where |
|--------|-------|
| `roster_id` = `m.roster_id` (no IFNULL) | `agent_coord/server/sql/sp_mail.sql` `mill_mail_get` |
| Drop `LEFT JOIN activity a` for roster fallback | same |
| `affn` join on `m.roster_id` only | same |
| Keep `sender_roster_id` / `saffn` on `m.roster_id` | same |

Also on this tip (docs-only cherry-pick): `docs/JOIN.md` + `docs/install/HOST.md`
from `20a81cc` (one invite door / connect rule / five verbs).

## Test

- `test_mail_get_card_roster_only` (new): null letter roster stays null even when activity still carries project.
- `test_perf_punch.test_floor_part_sql_joins_scope_table`: asserts `IFNULL` / `JOIN activity` absent from both `mill_mail_select` and `mill_mail_get`.
- Broader: `test_mail.py`, `test_roster_sp_punch.py`, `test_perf_punch.py` (throwaway DB).

No version bump in this claim. Do not ensure live books from unreleased tip.
