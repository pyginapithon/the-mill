# Claim - Wall UI absorb late/stale results into off-pane last-good (wow149)

Status: **superseded locally by wow150** (`CLAIM-wall-ui-reuse-inflight`). Was local WIP on `claim/floor-v1-parts`. Committed locally only. Not pushed. No mill-wall recycle (Operator).

Parent: wow148 fp-before-paint (`fca753a` / `CLAIM-wall-ui-fp-before-paint`).

## Lock

| Item | Lock |
|------|------|
| Live pane + current gen | Opaque Checking overlay; no overwrite until fp decide (wow148) |
| Stale gen / user clicked away | **Still USE** late payload: commit floor book + `_floor` + fp + off-pane DOM last-good |
| Live `.on` pane | Untouched by stale-gen settle |
| Return to pane | `wallRestoreActivePaneFromFloor({ force: true })` shows updated last-good under Checking; tick confirms |
| Keep | wow146-148, limit=50, lean, stagger, wall_perf, human readonly |

## Root cause

Switch-gen stale paths returned early without updating `window._floor` / off-pane last-good (or early painters skipped absorb entirely). Late isolate results were dropped, so the next visit still showed old content.

## What landed

1. **`boot.js` (wow149)** - `wallCommitFloorBook` / `wallPaintOffPaneLastGood` / `wallAbsorbOffPaneResult`; stale settle + onRow + early painters commit; restore `{force:true}` on enter.
2. **cache-bust `wow149`**, tests, this claim.

## Glance

1. Recycle mill-wall - **Operator**.
2. Hard-refresh `boot.js?v=wow149`.
3. Open MAIL, flip away before check finishes, wait, return - should show the late result (not the pre-leave snapshot only).
4. Active tab during late settle must not flash/blank.

## Out of scope

Push / recycle / Playwright.

## Roles only

Builder / wall-ui / Operator / Validator.
