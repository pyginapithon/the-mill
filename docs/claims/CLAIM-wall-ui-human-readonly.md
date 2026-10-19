# Claim - Wall UI human-readonly gate

Status: **local WIP** on `claim/loop-3-wall-mail-rooms`. Committed locally only. Not pushed.

Parent: Loop-3 Wall MAIL rooms / #40 wall-ui-perf-rebuild peers. Product: humans glance; agents `mill send` / `mill reply`.

## Lock

`WALL_HUMAN_READONLY` gate (default **ON**):

| Keep | Hide / inert |
|------|----------------|
| GET polls (`/api/floor`, tab parts, Activity, etc.) | Compose (`#mail-compose`, `#compose-overlay`, `#desk-form` POST `/api/desk`) |
| LIST / GRAPH / ROOMS glance paint | Rooms "Reply in thread" + `.sg-mail` open-compose |
| Filters / local chrome prefs | Plan park / edit issue POSTs |
| Admin refresh (GET) | Admin mint / LAN-on/off write actions |
| | Human mark-read POST |

Escape (dev / badge dogfood only): `localStorage.factory-human-readonly=off` **or** `?human_write=1`.

## What landed

1. **boot.js** - marker `WALL_HUMAN_READONLY`; `wallHumanReadonly()` / `wallApplyHumanReadonly()`; early class `html.wall-human-readonly` + `inert` on write chrome; gates on `setCompose`, `openMailPopup`, compose click, desk-form submit, `markMailReadHuman`, park/edit submit, `planPost`, `adminPost`, reply paint, keys `openCompose`.
2. **board.css** - hide selectors under `html.wall-human-readonly`.
3. **board.html** - `boot.js?v=wow135`; compose marked `data-human-write="1"`.
4. **Tests** - `tests/wall/test_wall_ui_human_readonly.py` (static source assertions; no Playwright).

## Evidence (path:lines)

- Marker + helpers: `agent_coord/web/wall_ui/default/boot.js` (head + `wallHumanReadonly` / `wallApplyHumanReadonly`)
- Compose / desk POST gates: same file (`setCompose`, desk-form submit, `openMailPopup`)
- Poll kept: `wallStartFloorPoll` / `fetch("/api/floor?"` unchanged for GET
- CSS: `agent_coord/web/wall_ui/default/board.css` (`html.wall-human-readonly ...`)
- Cache-bust: `agent_coord/web/wall_ui/default/board.html` `boot.js?v=wow135`

## Out of scope

- No Playwright; no Wall / mill-wall restart / www deploy / push
- No Loop-2 floor-fp / Builder SQL (parked under `~/.mill/wall_ui_save/`)
- Multi-To compose still out (agents own send/reply)

## Glance

1. Hard-refresh Wall (`boot.js?v=wow135`).
2. MAIL tab: no `+` compose; Rooms nest has no Reply-in-thread.
3. Network: 15s `GET /api/floor?...` still fires; no accidental `POST /api/desk` from chrome.
4. Escape check (optional): `localStorage.setItem('factory-human-readonly','off'); location.reload()` restores write chrome.
