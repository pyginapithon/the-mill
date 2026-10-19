# Claim - Wall UI content-aware Checking overlay (wow152)

Status: **superseded locally by wow153** (`CLAIM-wall-ui-floor-scroll`). Was local WIP on `claim/floor-v1-parts`. Committed locally only. Not pushed. No mill-wall recycle (Operator).

Parent: wow151 translucent-overlay (`d03c65b` / `CLAIM-wall-ui-translucent-overlay`).

## Lock

| Item | Lock |
|------|------|
| Last-good content under pane | **More translucent** Checking backdrop (~22% panel) so prior paint stays clearly visible |
| Empty pane (no underlying data) | **Opaque** solid cover (`.wall-pane-overlay.is-opaque`) - translucent over empty looks broken |
| Toggle | `wallShowPaneOverlay` uses `wallHasRealContent(host)` -> translucent vs `is-opaque` |
| Keep | fp-before-paint / reuse-inflight / absorb / switch-gen / keep-prior |

## What landed

1. **`shell.css`** - default overlay ~22% `color-mix`/`rgba`; `.is-opaque` solid `--panel`.
2. **`boot.js`** - `wallShowPaneOverlay` class toggle + `data-wall-overlay-mode`.
3. **cache-bust `wow152`**, tests, this claim.

## Glance

1. Recycle mill-wall - **Operator**.
2. Hard-refresh `shell.css?v=wow152` / `boot.js?v=wow152`.
3. Pane with rows: light veil + visible last-good. Empty pane: solid Checking cover.

## Out of scope

Push / recycle / Playwright. Leave Builder Loop-2 dirty unstaged.

## Roles only

Builder / wall-ui / Operator / Validator.
