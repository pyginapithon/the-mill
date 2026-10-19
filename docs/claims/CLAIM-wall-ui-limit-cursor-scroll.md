# Claim - Wall UI v1 mailbox+todos limit/cursor infinite-scroll + opaque subtab overlay (wow145)

Status: **superseded locally by wow146** (CLAIM-wall-ui-keep-prior-pane) for leave/return blank. wow145 limit/cursor + overlay remain. Local only; not pushed.

Parent: Builder SoR `6a7e7ed` (`WALL-CONTRACT-v1-limit-cursor` / `CLAIM-v1-limit-cursor`) + wall-ui lean wow144.

Evidence: Builder samples under `~/.mill/evidence/builder-v1-limit-cursor-20260926/`.

## Lock

| Item | Lock |
|------|------|
| First list/poll | `GET /api/v1/mailbox` + `/api/v1/todos` with explicit `?limit=50` |
| Scroll | Near-bottom on MAIL list cols + TODO list/board: if `next`, fetch `?limit=50&cursor=`, **append** (dedupe by `id`), keep `*_trunc` + detail-on-open |
| Subtab overlay | MAIL Rooms/List/Graph + TODO Nest/Board/List (and strip into those panes): **opaque** `.wall-pane-overlay` on `.pane-body` until tick confirms; **no blank** of prior content; no-change clears overlay and keeps paint |
| Keep | stagger wow143, lean wow144, two-phase, spinners, `wall_perf` opt-in, human readonly |
| Park | trees + mill todos #49-55 (other panes) |

## What landed

1. **`boot.js` (wow145)** - `limit=50` on v1 mailbox/todos first fetch; `wallRememberListNext` / `wallFetchListNextPage` / scroll wire; opaque `wallShowPaneOverlay` on `setMailView` / `setJobsView` / showTab mail|jobs; clear on no-change + confirmed tick.
2. **`shell.css`** - `.wall-pane-overlay` absolute opaque cover over `.pane-body`.
3. **`board.html` + static `board.html`** - `boot.js?v=wow145`, `shell.css?v=wow145`.
4. **Tests** - `tests/wall/test_wall_ui_limit_cursor_scroll.py`; cache-bust asserts bumped to wow145.
5. **This claim**.

## Behavior

| Action | Behavior |
|--------|----------|
| First poll / list | `?limit=50` (no cursor); store `next` |
| Near list/board bottom | if `next`, `?limit=50&cursor=<next>`; append rows; update `next` (null stops) |
| Open trunc row | unchanged wow144 detail GET |
| Switch MAIL/TODO subtab | opaque overlay; tick; if payload unchanged keep prior DOM and drop overlay |
| SESSION Now/Leases/Watch/History | **no** opaque overlay; strip into SESSION clears any leftover cover |

## Glance (host)

1. Recycle mill-wall so it serves this checkout (`MILL_WALL_SRC=git`) - **Operator**; wall-ui does not restart.
2. Hard-refresh Wall (`boot.js?v=wow145`).
3. MAIL / TODO: Network first isolate shows `limit=50`; scroll near bottom issues `cursor=`; rows append.
4. Flip Rooms/List/Graph or Nest/Board/List: opaque spinner over content; prior rows stay if poll finds no change.
5. Keep Rooms stagger; optional `?wall_perf=1`.

## Out of scope

- Push / mill-wall recycle / pack / PyPI / Playwright
- Other dense panes (#49-55) and progressive trees
- Builder SoR changes

## Roles only

Commits / docs / todos use Builder / wall-ui / Operator / Validator - no personal names or home paths.

