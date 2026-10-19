# Claim - Wall UI keep prior pane DOM + theme on subtab leave/return (wow146)

Status: **superseded locally by wow147** (`CLAIM-wall-ui-tab-switch-race`) for rapid-switch races. Keep-prior helpers remain. Local only; not pushed.

Parent: wow145 limit/cursor + opaque overlay (`ecb94e7`).

## Lock

| Item | Lock |
|------|------|
| Leave/return | NEVER blank/clear pane DOM on leave or re-enter for MAIL/TODO/FLOOR/SCORE/SESSION |
| Return | Keep prior painted content; opaque `.wall-pane-overlay` OK while confirming; no-change keeps old paint |
| Theme | Re-assert `data-theme` / density / rail chrome on tab enter; never remove domain CSS links |
| Keep | limit=50 scroll, lean detail-on-open, stagger, wall_perf opt-in, human readonly |

## What landed

1. **`boot.js` (wow146)** - `wallLoadingOnly` / fixed `wallHasRealContent` + `wallShowLoading` (no clobber); `wallPreserveThemeChrome`; `wallRestoreActivePaneFromFloor`; showTab overlays all strip panes; `board(..., {hereOnly:true})` for session agents ticks; `paintFloorView` skips inactive/empty wipe; rooms structureOnly no longer poisons nest with loading+content; removed rooms `src.innerHTML=""` blank.
2. **`shell.css` + board.html** - cache-bust `wow146`.
3. **Tests** - `tests/wall/test_wall_ui_keep_prior_pane.py`; cache-bust asserts bumped.
4. **This claim**.

## Behavior

| Action | Behavior |
|--------|----------|
| Leave any strip pane | Prior DOM stays; theme/chrome classes kept |
| Enter MAIL/TODO/FLOOR/SCORE/SESSION | Opaque overlay; spinner only if region truly empty; tick confirms |
| No-change tick | Drop overlay; restore from `_floor` if DOM was blanked |
| SESSION agents poll | Paints `#here` only - does not rewrite TODO kanban/list |

## Glance (host)

1. Recycle mill-wall so it serves this checkout (`MILL_WALL_SRC=git`) - **Operator**; wall-ui does not restart.
2. Hard-refresh Wall (`boot.js?v=wow146`).
3. Open MAIL (or TODO/FLOOR/SCORE/SESSION), wait for rows; flip to another strip tab and back - prior rows still painted under/after overlay.
4. Theme (light/dark/auto) and domain look stay across switches.
5. Keep Rooms stagger; optional `?wall_perf=1`; human readonly.

## Out of scope

- Push / mill-wall recycle / pack / PyPI / Playwright
- Builder SoR changes

## Roles only

Commits / docs / todos use Builder / wall-ui / Operator / Validator - no personal names or home paths.
