# Claim - Wall UI welcome JOIN paste + Invite Agent (wow169)

Status: **superseded locally by wow170** (split paste + Generate new URL). Still on claim/floor-v1-parts; not pushed.
Prior: wow168 MAIL Rooms scroll + recency sort.

## Roles only

No personal identifiers in commits, Claims, or docs - roles only (host, desk, human, agent).

## Lock

1. **Welcome opening surface (one BOX):** beat1 + paste-to-agent JOIN block + invite URL mint/copy. Strip Invite Agent is a shortcut into the same surface.
2. **Visits:** auto-open on new document loads / new tab-window only. SPA in-pane nav never reopens. Human can close anytime (Enter Nest). **Do not show again** -> `localStorage factory-welcome-hide=1` skips auto-open on future visits only. **Strip Invite Agent always reopens** the same full welcome kit.
3. **JOIN paste:** mint first (or reuse `desk`+`seat` from query), then fill Copy block with `mill join <invite_url>`.
4. **Invite URL shape (Builder provisional):** `https://<wall>/welcome?desk=<DESK_slug>&seat=<plaintext_once>`. Response fields when API ready: `invite_url`, `desk`, `seat` (once). One URL = one seat.
5. **Gate:** trust=high -> humans + Admin; trust=limited -> Admin only (detect admin desk/role/flag if present; else hide).
6. **Mint:** prefer POST `/api/v1/invite`; if absent, local stub templated URL. Human-readonly exception: mint only (no mail/todo writes).
7. **CSS budget:** shell.css stays under 16KB normalized; welcome/invite look lives lean in board.css.
8. **Cache-bust:** `boot.js?v=wow169` + test pin flips.

## What landed

1. **board.html** - `#wall-welcome` opening surface; `#wall-invite-box` strip shortcut; `boot.js?v=wow169`.
2. **boot.js** - marker `WALL_WELCOME_INVITE_WOW169`; parse desk/seat; stub/API mint; JOIN fill; visit dismiss + noshow; invite gate on trust.
3. **board.css** - lean welcome + invite styles.
4. **middleware.py** - serve board glass at `/welcome`.
5. **Tests** - pin flips wow168 -> wow169; `test_wall_ui_welcome_invite_wow169.py`.
6. **This claim**.

## Stub vs real API

- **Real (Builder tip bd3cacb):** POST `/api/admin/invites` body `{ "action":"mint_seat", "desk":"<slug>", owner, token }` -> `{ ok, desk, seat, invite_url, status:"ready" }` (seat once).
- **Stub only if** that endpoint returns **404** on the Wall tip (local-mill not recycled yet). Other errors surface in the note; no silent fake seat.
- Glass uses HTTP only (`mill invite --seat` is Loop-2 CLI).

## Glance (host)

1. Hard-refresh local-mill Wall (`boot.js?v=wow169`) or open `/welcome`.
2. Welcome BOX: beat1, JOIN pre, Copy, Enter Nest, Do not show again; Invite Agent mint when gate allows.
3. Mint (or open `/welcome?desk=slug&seat=once`) -> JOIN shows `mill join https://<wall>/welcome?desk=...&seat=...`.
4. Enter Nest without checkbox -> reload shows welcome again; with checkbox -> future visits skip.
5. SPA tab switches do not reopen welcome. Strip **Invite Agent** reopens the same BOX when gate on.
6. trust=limited without Admin chrome: mint section + strip hidden.

## Out of scope

- Push / pack / PyPI / Playwright / mill-wall recycle
- Builder `/api/v1/invite` server implementation
- skill.md / mill core beyond `/welcome` glass serve

## Tests run

- pytest tests/wall (cache-bust + welcome)
- python -m agent_coord.web.wall_ui.validate_assets
