# Claim - Wall floor poll lean parts (Loop-3)

Status: **local WIP** on `claim/loop-3-wall-mail-rooms`. Committed locally only. Not pushed.

## Lock

GET `/api/floor` polls must request **only the open tab's parts** - not the whole todo+score+mail book every 15s.

this machine: fat GET `/api/floor` (~400KB typical, p95 ~930ms, bursts 100+/sec) stalled verbs. AWS stays fine with smaller polls.

## Before / after `parts=`

| Open UI | Before (stripNeed concat) | After (tab core only) |
|---------|---------------------------|------------------------|
| SESSION (board default / now) | `agents,mail,scores,todos` | `agents` |
| MAIL list | `mail,agents,scores,todos` | `mail` |
| **MAIL Rooms** | `mail,trees,agents,scores,todos` | **`mail,trees`** |
| TODO Nest/List/Board | `todos,trees,agents,mail,scores` | `todos,trees` |
| SCORE | `scores,agents,mail,todos` | `scores` |
| FLOOR map | `agents,mail,scores,todos` | `agents,mail` |

Poll URL shape (unchanged wire):  
`GET /api/floor?<project|lan=...>&parts=<wallParts()>`  
Evidence: `agent_coord/web/wall_ui/default/boot.js` `wallParts` + fetch in `_tickBody`.

## Root cause

1. **Fat parts:** `wallParts()` appended `stripNeed = ["agents","mail","scores","todos"]` on every tab so strip KPI chips never went stale - that re-shipped the todo book (card bodies in `needs`/`issues`) and scores on MAIL/SESSION polls.
2. **Burst pile-up:** many callers (`showTab`, `setMailView(rooms)`, `selectRail`, `setFloorMode`, `setSessionMode`, boot, 15s timer) invoked async `tick()` with **no single-flight / debounce**, so overlapping fetches explained 100+/sec (not the 15s timer alone). Duplicate `setInterval` risk if boot re-entered.

Strip already had `_stripLast` for stale counts when a part is absent - stripNeed made that path dead.

## Fix (Wall UI only; Loop-2 floor slice API untouched)

- Drop `stripNeed` concat; `wallParts()` returns tab core only.
- Coalesce: `tick()` -> 50ms debounce + `_tickInflight` single-flight + one `_tickAgain` follow-up; `window.__wallFloorPoll` clears before `setInterval(tick, 15000)`.
- Gate heavy paints (`board` / `paintPlan` / `mail` / `cards` / session agents) on `raw.parts` so a seats-only or mail-only poll does not re-bind every card body into the DOM.

## Evidence (path:lines)

- `wallParts` tab-scoped return: `agent_coord/web/wall_ui/default/boot.js:890`-`:918` (`return core`)
- `_stripLast` keep strip when part absent: `boot.js:1463` + `strip` uses it
- tick coalesce: `boot.js:5879` `_tickInflight`, `:5883` `tick()`, `:5913` `_tickBody`
- fetch URL: `boot.js:5929` `parts=` + `encodeURIComponent(wallParts())`
- paint gate on slice parts: `boot.js:5982`-`:6002` (`sliceHas` -> board/mail/cards)
- single interval: `boot.js:6927`-`:6930` `__wallFloorPoll` clear+set
- Tests: `tests/wall/test_wall_floor_parts_poll.py` (4 passed locally)

## Remaining burst / lean risk

- **Jobs tab** still ships full todo card bodies (`detail`/`doing`/`progress`) every 15s - no Loop-2 lean-todos part flag; do not invent one here (Builder if needed).
- **MAIL tab** still ships full letter bodies for the mailbox part (needed for list/rooms nest).
- Coalesce stops overlapping client polls; server-side fan-out from many browser tabs / hard-refresh storms can still burst.
- Strip KPI chips for unvisited books stay at last-seen (`_stripLast`) until that tab is opened once.

## Out of scope

- Loop-2 `agent_coord/server/records/floor.py` parts API
- Push / Wall service restart (hard refresh loads `boot.js`)
- `wall_ui_save/` mirrors
