# Claim - Wall UI fingerprint-before-paint + Checking overlay (wow148)

Status: **superseded locally by wow149** (`CLAIM-wall-ui-absorb-off-pane`) for late/stale off-pane absorb. fp-before-paint remains. Local only; not pushed.

Parent: wow147 tab-switch generation (`a3b1b7e` / `CLAIM-wall-ui-tab-switch-race`) + wow146 keep-prior.

## Lock (human-owned UX)

| Item | Lock |
|------|------|
| Before fp decide | Do **not** paint/overwrite live DOM (no early isolate paint, no provisional ensure*Paint) |
| While checking | Opaque `.wall-pane-overlay` only ("Checking..."); last-good stays underneath |
| Fp same / hash same | Keep last result; drop overlay |
| Fp different / hash change | Paint confirmed parts, **then** drop overlay |
| Keep | switch-gen, keep-prior, limit=50 scroll, lean, stagger, wall_perf, human readonly |

## Root cause

Progressive early painters (`wallPaintMailRoomsEarly` / `wallPaintTodosEarly` / `wallPaintFloorPartEarly` / mailbox `mail(d)`) and showTab `ensure*Paint` / `paintHero` / `wallMarkTabLoading` mutated panes **before** tick fingerprint/hash settle. That overwrote last-good with provisional/empty content under rapid switches.

## What landed

1. **`boot.js` (wow148)** - early paths absorb-only; Checking overlay; MarkTabLoading no-ops under overlay; showTab loads domain CSS/JS only; settle paints then clears overlay; no-change keeps last result.
2. **`board.html` + `shell.css`** - cache-bust `wow148`.
3. **Tests** - `tests/wall/test_wall_ui_fp_before_paint.py`.
4. **This claim**.

## Glance (host)

1. Recycle mill-wall (`MILL_WALL_SRC=git`) - **Operator**.
2. Hard-refresh (`boot.js?v=wow148`).
3. Flip tabs quickly: opaque Checking overlay; prior rows stay until confirm; no empty flash.
4. Keep Rooms stagger; optional `?wall_perf=1`.

## Out of scope

- Push / mill-wall recycle / pack / PyPI / Playwright

## Roles only

Builder / wall-ui / Operator / Validator - no personal names or home paths.
