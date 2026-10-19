# CLAIM wall-ui-welcome-show-before-mint-wow172

## Bug
`wallWelcomeBoot` awaited `wallMintInvite` when `_wallInviteGateOk` before `wallWelcomeShow`.
If mint hung (slow/unreachable `/api/admin/invites`), Host never saw the Nest welcome popup.
Playwright/default gate was often false (no admin/high trust), so mint was skipped and show was immediate - tests hid the hang.

## Repro (before wow172, boot.js?v=wow171)
- gate false + hang mint: popup visible (inviteOk=0, no mint request)
- gate true + hang mint: popup stayed hidden (`hungWithoutShow=true`, pollsHiddenFalse=0, mint_request fired)

## Fix
Show FIRST, then mint in background via `Promise.resolve().then(() => wallMintInvite(...))`.
Marker `WALL_WELCOME_SHOW_BEFORE_MINT_WOW172`; cache bust `boot.js?v=wow172`.

## Repro (after)
- gate true + hang mint: popup visible at ~400ms while mint still pending (`showBeforeMintRespond=true`)
- gate true + 3s mint: show at ~394ms; mint_respond at ~3338ms

## Tests
`tests/wall/test_wall_ui_welcome_show_before_mint_wow172.py` (replaces wow171) - 10 passed.
Evidence: `.mill/evidence/validator-wow172/`.

Superseded for dismiss paths by CLAIM-wall-ui-welcome-dismiss-always-wow173.md.
