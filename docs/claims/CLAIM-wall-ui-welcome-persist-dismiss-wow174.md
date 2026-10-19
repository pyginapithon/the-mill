# CLAIM wall-ui-welcome-persist-dismiss-wow174

## Bug
After wow173, Nest dismiss (Escape / Enter Nest / backdrop / X) hid `#wall-welcome`
but did **not** set `factory-welcome-hide=1` (Enter Nest only persisted when the
"Do not show again" checkbox was checked; Escape/X/backdrop always passed `persist=false`).
Host console `.hidden=true` likewise skipped persist. Refresh auto-opened welcome again
and retrapped Host. Landing on `?welcome=1` force-opens every load even when hide is set.

## Fix (smallest live glass tweak)
- Enter Nest / Escape / X / backdrop dismiss **always** set `factory-welcome-hide=1`.
- `wallWelcomeDismiss()` defaults `persist=true`.
- On dismiss, strip `welcome` query via `history.replaceState` so `?welcome=1` does not
  force-reopen after refresh.
- Marker `WALL_WELCOME_PERSIST_DISMISS_WOW174`; cache-bust `boot.js?v=wow174`.

## Host (if already dismissed without persist)
Click **Enter Nest** once, **or** in console:
```js
localStorage.setItem("factory-welcome-hide", "1");
// optional: strip force-open qs
history.replaceState(null, "", location.pathname + location.search.replace(/[?&]welcome=[^&]*/,"").replace(/^&/,"?") + location.hash);
```
Then reload. Do **not** rely on `document.getElementById("wall-welcome").hidden = true`
alone - that does not persist across document load.

## Tests
`tests/wall/test_wall_ui_welcome_persist_dismiss_wow174.py` (replaces wow173 welcome pin).
Cache-bust pins flipped wow173 -> wow174 across wall UI tests.

## Out of scope
Push / pack / PyPI / mill-wall recycle.
