# Claim - Wall UI welcome as Nest popup overlay (wow171)

Status: **local WIP** on claim/floor-v1-parts. Committed locally only. Not pushed. Not pack/PyPI. No Playwright.
Prior: wow170 welcome split workstation once vs invite-only + Generate URL.

## Roles only

No personal identifiers in commits, Claims, or docs - roles only (host, desk, human, agent).

## Lock

1. **Popup on Nest (not a separate /welcome page feel):** `#wall-welcome` is a translucent overlay on Nest glass. Nest remains visible under `.ww-backdrop` (rgba ~0.55). Card is a floating popup (box-shadow, scroll).
2. **Full kit kept:** beat1; Workstation once; This agent JOIN+invite; Generate new URL; Enter Nest close; Do not show again; strip Invite Agent reopen.
3. **ALWAYS auto-open** on new window/tab document load unless Do not show again (`factory-welcome-hide`). SPA in-pane nav never reopens. Strip Invite Agent always reopens full kit.
4. **`/welcome` route:** still serves Nest board; opens popup; `history.replaceState` to `/` (keep query) so URL feels like Nest. `?welcome=1` also forces open.
5. **Gate / mint / split paste:** unchanged from wow170 (high=humans+Admin; limited=Admin; mint_seat; Workstation once vs This agent).
6. **CSS budget:** shell.css stays under 16KB normalized; welcome look lean in board.css.
7. **Cache-bust:** `boot.js?v=wow171` + test pin flips.

## What landed

1. **board.html** - `.ww-backdrop` + `data-wall-welcome-overlay`; `boot.js?v=wow171`.
2. **boot.js** - marker `WALL_WELCOME_NEST_POPUP_WOW171`; always-auto-open comments; `/welcome` replaceState to `/`; `?welcome=1` force.
3. **board.css** - translucent backdrop + popup card shadow (Nest shows through).
4. **Tests** - pin flips wow170 -> wow171; `test_wall_ui_welcome_nest_popup_wow171.py`.
5. **This claim** (wow170 claim marked superseded locally).

## Glance (host)

1. Hard-refresh local-mill Wall (`boot.js?v=wow171`) or open `/welcome` (Nest URL becomes `/`).
2. Popup overlays Nest (Nest chrome visible through dim). Full kit: beat1; Workstation once; This agent; Enter Nest; Do not show again; Invite Generate new URL when gate on.
3. New window/tab always shows popup unless Do not show again was checked earlier.
4. Enter Nest without checkbox -> next new document shows popup again; with checkbox -> future visits skip auto-open.
5. SPA tab switches do not reopen. Strip **Invite Agent** reopens the same popup when gate on.

## Out of scope

- Push / pack / PyPI / Playwright / mill-wall recycle
- skill.md / mill core beyond welcome glass

## Tests run

- pytest tests/wall (cache-bust + welcome nest popup)
- python -m agent_coord.web.wall_ui.validate_assets

Superseded for mint-ordering by CLAIM-wall-ui-welcome-show-before-mint-wow172.md.
