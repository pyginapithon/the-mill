# Claim - Loop-3 Wall MAIL rooms lean cast

Status: **local WIP** on `claim/loop-3-wall-mail-rooms`. Committed locally only if clean. Not pushed.

## Lock

Wall MAIL LIST / GRAPH / ROOMS paint lean public MAIL from floor:

- Letter: `sender{deskId,roster}` + `mail_tos[{deskId,roster,receipt}]`
- Room cast = sender ∪ mail_tos (parentage stays in TREE; no `mail.parent_id`)
- No `opened` on the public cast
- Agents own `mill send` / `mill reply`; Wall compose stays **single-To** this pass

## Unread / attention choice (document)

Do **not** invent agent-unread from missing `opened`.

| Signal | Wall use |
|--------|----------|
| `mail_tos[].receipt == 1` | Needs human / attention (HR; mill send no longer sets it, #254) |
| legacy `reads` / `readers` / `read_agent` | Dual-read contract when present |
| `floor.desk_unread` | SESSION / rail badges (floor already gives) |
| TREE crumbs / nest | Rooms nest paints HR + payload unread when present |

Lean rows without reads -> `mail_msg_agent_unread` is **False**; attention = receipt HR.

## Evidence (path:lines)

- SoR lean adapters: `agent_coord/web/wall_logic/mail.py:33` `mail_is_lean`, `:40` `mail_sender_desk`, `:52` `mail_tos`, `:187` `mail_room_cast`, `:208` `mail_dst_desks`, `:219` `mail_at`, `:357` receipt HR, `:372` no invent unread
- SoR rooms: `:84` `mail_tree_root` (WHERE type='mail' AND lft=1; no GROUP BY), `:119` `mail_rooms_from_trees`, `:141` crumbs-only `mail_tree_depth0`
- JS mirror: `agent_coord/web/wall_ui/default/mail/mail.js:12`-`:291`
- Paint: `agent_coord/web/wall_ui/default/boot.js` `paintMailRooms` (:3916), LIST/GRAPH/rooms nest cast (~3639-3881), floor edges (~2636)
- Help: `agent_coord/web/wall_ui/default/board.html` MAIL help lean copy
- CSS: `agent_coord/web/wall_ui/default/board.css` rooms cast polish
- Tests: `tests/wall/test_mail_rules.py:263` `test_lean_adapters_*`, `:283` receipt HR, `:296` lean LIST/srcs

## Glance

1. Prefer office LAN: `https://192.0.2.10/`
2. DevTools -> Application -> Local Storage -> set `factory-mail-view` = `rooms`
3. Hard refresh; MAIL -> Rooms. Expect TREE roots left, nest + cast labels right; compose still single-To.

## Out of scope this pass

- Multi-To / reply-all Wall compose
- Loop-2 product features / pack / PyPI / push
- `wall_ui_save/` and stale `static/board.html`
- Restart Wall / Windows service
- Touching `agent_coord/server/sql/tables.sql` (left on claim/34 stash)

## Glance evidence

- Screenshot: tmp/loop3-glance/mail-rooms-root.png (PT 2026-09-26 ~05:11)
- Live https://192.0.2.10/ with localStorage.factory-mail-view=rooms
- Observed note: lean MAIL cast copy; data-mail-view=rooms; Rooms toggle on
- Live Wall served note from this working tree (no service restart). Pack/www sync not required for this host path.

## Tests run

- pytest tests/wall/test_mail_rules.py - all pass (incl. lean adapters + Rooms root SELECT type=mail AND lft=1)
- 
ode --check on mail.js + oot.js - ok
- scripts/wall_css_js_check.py - pre-existing KeyError on keys.js (not introduced here)


## MAIL room root (Builder product lock)

Proof: `agent_coord/server/sql/sp_tree.sql` + Rooms SoR.

Exact Rooms root query (no GROUP BY)::

```sql
SELECT name_id, type, id, lft, rgt
FROM tree
WHERE type = 'mail' AND lft = 1
ORDER BY name_id;
```

- Root per forest is `lft=1` (`mill_tree_create`). `type='mail'` for MAIL rooms only.
- Optional: `JOIN name n ON n.id = tree.name_id` for TREE_* slug label.
- Index: `KEY idx_type_lft (type, lft)` - added specifically to drop GROUP BY; Rooms filter stays `WHERE type = 'mail' AND lft = 1 ORDER BY name_id`.
- Client-side (`floor.trees`): keep trees whose root node is `type=mail` and `lft=1`.
- Room identity = `name_id` (`floor.trees[].name` / TREE_* slug).
- Nest / crumbs via lft/rgt under that root on the same name_id. **Depth-0 helper is crumbs-only** inside one name_id (`mail_tree_depth0`), not Rooms list.
- Keep lean cast (sender U mail_tos; receipt=HR; no invent unread from missing opened).

### Evidence (path:lines)

- SoR: `agent_coord/web/wall_logic/mail.py:84` `mail_tree_root`, `:119` `mail_rooms_from_trees`, `:141` `mail_tree_depth0`
- JS: `agent_coord/web/wall_ui/default/mail/mail.js:44` `mailTreeRoot`, `:57` `mailRoomsFromTrees`, `:63` `mailTreeDepth0`
- Paint: `agent_coord/web/wall_ui/default/boot.js:3713` `mailTreesWithMail`, `:3725` `mailRoomTreeRoot`, `:3916` `paintMailRooms`, `:3869` `mailRoomsNestHtml`
- Tests: `tests/wall/test_mail_rules.py:313`-`:381`


## Cast count on Rooms nest (host)

Product: show **cast count = 1 (sender) + len(mail_tos)** on each mail in Rooms nest.
Hover/title lists sender + each mail_to desk/roster (not mail_tos alone).
Rail: room meta appends root cast N when lean; button title includes cast tip.

Floor already carries lean `mail_tos` via `public_mail` - do not invent if absent.

### Evidence (path:lines)

- Floor mailbox lean: `agent_coord/server/records/mail.py:211` `public_mail` (`mail_tos` at `:242`); floor paint `agent_coord/server/records/floor.py:400` / `:605`
- SoR: `agent_coord/web/wall_logic/mail.py:208` `mail_lean_tos_len`, `:218` `mail_cast_count` (= 1 + len), `:225` `mail_cast_tip`
- JS: `agent_coord/web/wall_ui/default/mail/mail.js:110` `mailLeanTosLen`, `:115` `mailCastCount`, `:120` `mailCastTip`
- Nest paint: `agent_coord/web/wall_ui/default/boot.js:3900`-`:3909` (`cast N` + tip)
- Rail summary: `boot.js:3862`-`:3865` meta `N msgs / cast k`; room tip `:3865`; root cast fill `:3948`-`:3959`
- CSS: `agent_coord/web/wall_ui/default/board.css:1638` `.dst.cast-n`
- Tests: `tests/wall/test_mail_rules.py:289` `test_lean_cast_count_and_tip`
