# Claim - Wall UI Wave 3 cold trim + Rooms tick skip (#40)

Status: **local WIP** on `claim/loop-3-wall-mail-rooms`. Committed locally only. Not pushed.

Parent: cloud-mill todo **wall-ui-perf-rebuild** (#40).

## Lock

Lessen tick / cold weight without inventing floor `parts=`. No Playwright. No Wall restart.

## What landed (Wave 3)

1. **board.html chrome** - lib + floor scripts `defer` (order kept before `boot.js`); GUIDE prose moved to inert `<template id="wall-lazy-guide">`, hydrated on first GUIDE open (`loadGuide`).
2. **Rooms left rail** - `mailRoomsTreesSig(trees)` fingerprint; skip `dstCol.innerHTML` rewrite when trees + mode/q/selection unchanged (mailbox badge churn alone does not rebuild rail).
3. **Rooms nest** - `mailRoomsNestSig` skip when selected room nest unchanged.
4. **No-op tick paint** - `ensureMailPaint` no longer rAF-double-calls `mail()`; when tick already `sliceHas("mail")` painted, pane path is `{ chromeOnly: true }`.
5. **Poll note** - 15s `wallStartFloorPoll` kept; comment marks path to event-driven / longer interval / kill timer later.

## Rooms refresh (Host ask)

| Item | Behavior |
|------|----------|
| Interval | `setInterval(tick, 15000)` via `wallStartFloorPoll` (paused when `document.hidden`) |
| Path | `_tickBody` -> `sliceHas("mail")` -> `mail(d)` -> `paintMailRooms` when `mailView==="rooms"` |
| Full payload skip | `_floorHash` early return when raw floor JSON + rail pick unchanged |
| Rail rewrite | Skipped when `mailRoomsTreesSig` + mode/q/selection match prior |
| Nest rewrite | Skipped when nest fingerprint unchanged |
| Still ships bodies | Yes - `parts=mail` / `mail,trees` via `public_mail` includes `body` |

## Builder ask (API - STOP, do not invent)

MAIL / Rooms still receives **full letter bodies** on every mail poll (`public_mail` -> `body`). A lean list / Rooms rail without bodies needs a **new** floor `parts=` flag (e.g. meta-only mailbox). **Do not invent here.** Hand to Builder if this machine still stalls on MAIL body bytes.

## Evidence (path:lines)

- `agent_coord/web/wall_ui/default/board.html` - defer libs; `wall-lazy-guide`; boot `?v=wow133`
- `agent_coord/web/wall_ui/default/boot.js` - `mailRoomsTreesSig`, `_mailRoomsRailSig`, `mailRoomsNestSig`, `ensureMailPaint({chromeOnly})`, poll future note
- Tests: `tests/wall/test_wall_ui_wave3_perf.py`

## Out of scope

- No Playwright; no Wall / mill-wall restart / www deploy
- No Loop-2 `floor.py` parts API
- Not killing the 15s timer this wave (note only)

## Hold

`mill hold --office cloud-mill the-mill agent_coord/web/wall_ui` during edit; drop after commit.
