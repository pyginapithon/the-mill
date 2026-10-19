# CLAIM wall-ui-welcome-dismiss-always-wow173

## Bug
After wow172, Host saw Nest welcome overlay but could not reliably escape it.
Escape had no welcome handler; backdrop click did nothing; no X close control.
Enter Nest already called `wallWelcomeHide`, but Host still felt stuck when mint
was pending (and Escape/backdrop expected to dismiss did not).

## Fix (smallest live glass tweak)
- Escape always dismisses `#wall-welcome` when visible (no persist).
- Enter Nest always dismisses even if mint still pending.
- Backdrop click dismisses.
- Header X (`#wall-welcome-x`) dismisses.
- Export `window.wallWelcomeHide` / `window.wallWelcomeDismiss` for Host console.
- Card `z-index:1` above backdrop; backdrop `cursor:pointer`.
- Marker `WALL_WELCOME_DISMISS_ALWAYS_WOW173`; cache-bust `boot.js?v=wow173`.

## Host console (immediate escape without refresh)
```js
document.getElementById('wall-welcome').hidden = true;
// or: wallWelcomeHide(false)
```

## Tests
`tests/wall/test_wall_ui_welcome_dismiss_always_wow173.py` (replaces wow172 welcome pin).
Cache-bust pins flipped wow172 -> wow173 across wall UI tests.

## Out of scope
Push / pack / PyPI / Playwright / mill-wall recycle.

Superseded for persist-on-dismiss + strip ?welcome=1 by CLAIM-wall-ui-welcome-persist-dismiss-wow174.md.
