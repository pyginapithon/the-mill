# Claim - Wall UI welcome split workstation once vs invite-only (wow170)

Status: **superseded locally by wow171** (Nest popup overlay + always auto-open). Still on claim/floor-v1-parts; not pushed.
Prior: wow169 welcome JOIN paste + Invite Agent strip.

## Roles only

No personal identifiers in commits, Claims, or docs - roles only (host, desk, human, agent).

## Lock

1. **Split paste copy (two cards):**
   - **Card A - Workstation once:** `pip install -U the-mill` + skill.md copy + restart. First agent on that workstation only.
   - **Card B - This agent:** `mill join <invite_url>` + `mill connect ...`. Invite URL only path for every agent (including other agents on the same workstation).
2. **Generate new URL:** button calls POST `/api/admin/invites` `mint_seat` again; refreshes invite URL in UI; one seat per agent.
3. **Visits / strip:** keep close, Do not show again (`factory-welcome-hide`), strip Invite Agent always reopens full welcome kit. SPA in-pane nav never reopens.
4. **Gate:** trust=high -> humans + Admin; trust=limited -> Admin only (unchanged).
5. **Mint:** POST `/api/admin/invites` body `{ action:"mint_seat", desk, owner, token }` -> `{ ok, desk, seat, invite_url, status:"ready" }`. Stub only on 404.
6. **CSS budget:** shell.css stays under 16KB normalized; welcome look lean in board.css.
7. **Cache-bust:** `boot.js?v=wow170` + test pin flips.

## What landed

1. **board.html** - two paste cards + Generate new URL label on mint; `boot.js?v=wow170`.
2. **boot.js** - marker `WALL_WELCOME_SPLIT_WOW170`; `wallWelcomeWorkstationText` + slim `wallWelcomeJoinText`; remint via existing `wallMintInvite`.
3. **board.css** - lean `.ww-paste` spacing.
4. **Tests** - pin flips wow169 -> wow170; `test_wall_ui_welcome_split_wow170.py`.
5. **This claim** (wow169 claim marked superseded locally).

## Glance (host)

1. Hard-refresh local-mill Wall (`boot.js?v=wow170`) or open `/welcome`.
2. Welcome BOX: beat1; **Workstation once** copy; **This agent** copy (join+connect); Enter Nest; Do not show again.
3. Invite (when gate allows): desk + **Generate new URL** remints seat and refreshes Card B + invite URL pre.
4. Enter Nest without checkbox -> reload shows welcome again; with checkbox -> future visits skip.
5. SPA tab switches do not reopen. Strip **Invite Agent** reopens the same BOX when gate on.

## Out of scope

- Push / pack / PyPI / Playwright / mill-wall recycle
- skill.md / mill core beyond welcome glass

## Tests run

- pytest tests/wall (cache-bust + welcome split)
- python -m agent_coord.web.wall_ui.validate_assets
