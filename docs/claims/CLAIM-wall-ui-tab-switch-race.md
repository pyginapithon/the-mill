# Claim - Wall UI tab/subtab switch generation guard (wow147)

Status: **superseded locally by wow148** (`CLAIM-wall-ui-fp-before-paint`) for fp-before-paint. Gen guard remains. Local only; not pushed.

Parent: wow146 keep-prior pane (`ac487ce` / `CLAIM-wall-ui-keep-prior-pane`).

## Lock

| Item | Lock |
|------|------|
| Generation | Every main-tab / MAIL|TODO|SESSION|FLOOR subtab switch bumps `_wallSwitchGen`; only matching gen may paint or clear overlays |
| Stale tick | Superseded `_tickBody` / early-paint / domain-ensure no-op DOM; may absorb into floor book; must NOT blank or clear overlay |
| Keep-prior | Last-good restore under opaque overlay on enter (wow146 helpers kept) |
| Theme | `wallPreserveThemeChrome` on bump + settle |
| Keep | limit=50 scroll, lean detail-on-open, stagger, wall_perf opt-in, human readonly |

## Root cause

Rapid main-tab + subtab clicks left an in-flight `tick()` (coalesced via `_tickInflight`/`_tickAgain`) to finish for the **previous** parts slice. That stale completion still painted (sometimes empty) and called `wallClearActivePaneOverlay()`, dropping the newer tab's overlay and leaving an empty pane. Domain `wallEnsureDomain().then(ensure*Paint)` and early isolate painters raced the same way. Once blank, fp/no-change skip kept it empty.

## What landed

1. **`boot.js` (wow147)** - `wallBumpSwitchGen` / `wallSwitchGenAlive` / `wallBeginTickGen` / `wallTickGenAlive`; showTab/setMailView/setJobsView/setSessionMode/setFloorMode bump; `_tickBody` captures gen and returns before paint/overlay-clear when stale; early painters + onRow gated; domain-ensure callbacks gen-gated; restore last-good under overlay on enter.
2. **`board.html` + `shell.css`** - cache-bust `wow147`.
3. **Tests** - `tests/wall/test_wall_ui_tab_switch_race.py`; cache-bust asserts bumped.
4. **This claim**.

## Behavior

| Action | Behavior |
|--------|----------|
| Fast tab/subtab flip | Newer switch owns gen; stale tick absorbs only; prior DOM + theme stay |
| Settle current gen | Paint if changed; no-change keeps prior; drop overlay |
| Enter pane | Restore last-good if empty, then opaque overlay, then tick |

## Glance (host)

1. Recycle mill-wall (`MILL_WALL_SRC=git`) - **Operator**; wall-ui does not restart.
2. Hard-refresh (`boot.js?v=wow147`).
3. Rapidly alternate SESSION/FLOOR/TODO/SCORE/MAIL and Rooms/List/Graph or Nest/Board/List - panes must not go empty; theme stays.
4. Keep Rooms stagger; optional `?wall_perf=1`.

## Out of scope

- Push / mill-wall recycle / pack / PyPI / Playwright
- Builder SoR changes

## Roles only

Commits / docs / todos use Builder / wall-ui / Operator / Validator - no personal names or home paths.
