# Claim - Wall UI opt-in perf instrumentation

Status: **local WIP** on `claim/floor-v1-parts`. Committed locally only. Not pushed.

Parent: wall-ui-perf-rebuild / cold-load diagnose (pre two-phase rail).

## Lock

Opt-in only. **ZERO cost when off**: `lib/perf.js` is not fetched unless `?wall_perf=1` or `localStorage.wall_perf=1`. No marks, no fetch wrap, no timers, no HUD on the default path. boot.js hooks are `typeof wallPerfFirst === "function"` guards only (undefined when gate off).

## What landed

1. **board.html** - `WALL_UI_PERF_GATE` inline injector; `boot.js?v=wow137`.
2. **lib/perf.js** - `performance.mark` / `measure`; thin `fetch` wrapper for `/api/v1/*` + `/api/floor` (bytes via Content-Length or clone); `console.table` dump; `wallPerfFirst`.
3. **boot.js** - first-populate hooks: `mail_rooms_rail`, `mail_rooms_body`, `mailbox_body` (no-op unless perf loaded).
4. **static/board.html** - `boot.js?v=wow137` for consistency.
5. Tests cache-bust asserts bumped wow136 -> wow137.

## Enable

- URL: `?wall_perf=1` (hard-refresh Wall)
- Or: `localStorage.setItem('wall_perf','1'); location.reload()`
- Dump: DevTools console `console.table` (~3s after load, or sooner after first mail paint). Manual: `wallPerfDump()`.

## Marks that fire (when on)

| Name | When |
|------|------|
| `boot` | perf.js load -> window load |
| `fetch:api_v1_*#N` / `fetch:api_floor#N` | each tracked GET (ms + optional bytes) |
| `first_mail_rooms_rail` | first Rooms left-rail populate |
| `first_mail_rooms_body` | first Rooms nest/body populate |
| `first_mailbox_body` | first LIST/GRAPH mailbox body populate |

## Evidence (path:lines)

- Gate: `agent_coord/web/wall_ui/default/board.html` (`WALL_UI_PERF_GATE`, `boot.js?v=wow137`)
- Lib: `agent_coord/web/wall_ui/lib/perf.js` (`WALL_UI_LIB_PERF`)
- Hooks: `agent_coord/web/wall_ui/default/boot.js` (`wallPerfFirst` after rooms rail/nest + mailbox list paints)
- Cache-bust tests: `tests/wall/test_wall_ui_floor_fp.py`, `test_wall_ui_floor_v1_consume.py`, `test_wall_ui_human_readonly.py`

## Out of scope

- No Playwright; no mill-wall restart / www deploy / push
- Two-phase Rooms rail: see CLAIM-wall-ui-mail-rooms-two-phase.md (wow138)
- Humans stay readonly; no DB writes

## Slow-load note (already known)

Top remaining cold costs: MAIL still ships full letter **bodies** on poll (`parts=mail` / v1 mailbox); Rooms may also pull tree-mail; 15s floor poll kept. Lean meta-only mailbox needs Builder `parts=` - do not invent here.
