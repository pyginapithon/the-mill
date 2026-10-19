# Claim - Wall UI lean mailbox+todos detail-on-open (wow144)

Status: **local WIP** on `claim/floor-v1-parts`. Committed locally only. Not pushed. No mill-wall recycle (Operator).

Parent: Builder lean SoR `fca60f2` (`WALL-CONTRACT-lean-mailbox-todos`) + wall-ui Rooms stagger wow143 (`de1c278`).

Evidence samples: `~/.mill/evidence/builder-cold-sql-quick-20260926/` (`sample-v1-*-lean.json`, `sample-v1-*-one.json`, `WALL-UI-LEAN-CONSUME.md`).

## Lock

List/poll already returns snippets (`body` / `doing`+`detail` <=256 + `*_trunc`). Glass paints those snippets. When the human **opens** a truncated mail letter or todo card, wall-ui GETs the detail route, replaces the local `_floor` row (drops trunc flags), and re-paints that surface.

Keep: stagger wow143, two-phase Rooms paint, strip/domain spinners, `wall_perf` opt-in, human readonly. No push / Playwright / pack / PyPI / service restart.

## What landed

1. **`boot.js` (wow144)** - lean helpers: `wallMailIsTrunc` / `wallTodoIsTrunc`, find+merge, `wallOpenMailIfTrunc` / `wallOpenTodoIfTrunc`.
2. **Open path** - click mail list row, Rooms nest `.mail-room-msg`, or `[data-todo-id]` card/list row: if trunc, `GET /api/v1/mail/{id}` or `GET /api/v1/todo/{id}`, merge, `mail()` / `board()` re-paint.
3. **Paint attrs** - `data-body-trunc` on mail rows; `data-todo-id` + `data-todo-trunc` on todo cards/list rows.
4. **board.html / static board.html** - `boot.js?v=wow144`.
5. **Tests** - `tests/wall/test_wall_ui_lean_mailbox_todos.py`; cache-bust asserts bumped to wow144.
6. **This claim**.

## Behavior

| Surface | List/poll | Open (click) |
|---------|-----------|--------------|
| Mail list / Rooms nest | paint `body` as returned; `data-body-trunc` | if `body_trunc`, GET `/api/v1/mail/{id}` -> merge `mail`, drop `body_trunc`, `mail(_floor)` |
| Todo card / list row | paint `doing`/`detail` as returned; `data-todo-trunc` | if `doing_trunc` or `detail_trunc`, GET `/api/v1/todo/{id}` -> merge into needs/issues, drop flags, `board(_floor)` |
| Flags absent | list payload already full | no detail fetch |

## Evidence (path:lines)

`agent_coord/web/wall_ui/default/boot.js`:

- Floor v1 lean comment: `1153:1154`
- needCard `data-todo-id` / trunc: `2497:2505`
- todo-list-row `data-todo-id`: `3020:3025`
- mail list `data-body-trunc`: `4304:4306`
- Rooms nest `data-body-trunc`: `4630:4632`
- lean helpers + open fetch/merge: `7063:7200`
- click open wire (list + rooms + todo): `7295:7345`
- Cache-bust: `agent_coord/web/wall_ui/default/board.html` `boot.js?v=wow144`
- Tests: `tests/wall/test_wall_ui_lean_mailbox_todos.py` (+ wow144 bumps in floor/v1/human/rooms/progressive)

## Glance (host)

1. Recycle mill-wall so it serves this checkout (or confirm `MILL_WALL_SRC=git` already points here) - **Operator**; wall-ui does not restart.
2. Hard-refresh Wall (`boot.js?v=wow144`).
3. MAIL list or Rooms: truncated letters show snippet; click opens detail fetch (Network: `/api/v1/mail/{id}`) then body expands.
4. TODO board/list: truncated cards show snippet; click fetches `/api/v1/todo/{id}` then full doing/detail.
5. Keep Rooms stagger: mailbox still after rooms+tree-mail. Optional `?wall_perf=1`.

## Out of scope

- Push / mill-wall recycle / pack / PyPI / Playwright
- `?fp=` client wire (documented; may land later)
- Progressive trees / dropping rooms from trio
- Builder SoR changes

## Roles only

Commits / docs / todos use Builder / wall-ui / Operator / Validator - no personal names or home paths.
