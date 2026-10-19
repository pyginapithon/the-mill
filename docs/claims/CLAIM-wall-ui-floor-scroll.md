# Claim - Wall UI floor/activity infinite scroll + scrollable Checking (wow153)

Status: **superseded locally by wow154** (`CLAIM-wall-ui-events-scroll`). Was local WIP on `claim/floor-v1-parts`. Committed locally only. Not pushed. No mill-wall recycle (Operator).

Parent: Builder #49-54 SoR (`600fdf1` / `WALL-CONTRACT-v1-limit-cursor` / `CLAIM-floor-limit-other-panes`) + wow152 overlay (`8076a6b`).

## Lock

| Item | Lock |
|------|------|
| First poll | Floor pageable parts + `/api/activity` use explicit `?limit=50` |
| Scroll panes | SESSION Now (`agents`/`#here`), Leases (`holds`/`#stations`), Watch (`watchers`), SCORE (`scores`), activity diary (`#wire-log`) + existing MAIL/TODO |
| Events | wow154 wires `parts=events` scroll after Builder `097af3c` |
| Checking overlay | Translucent: `pointer-events: none` so last-good stays **scrollable**; opaque empty cover stays blocking |
| Keep | wow146-152 paint locks, lean trunc, detail-on-open, reuse-inflight, absorb |

## What landed

1. **`boot.js`** - extend `wallRememberListNext` / `wallFetchListNextPage` / append+paint for agents/scores/holds/watchers/activity; wire scroll hosts; floor/activity `limit=50`.
2. **`shell.css`** - translucent overlay + chip `pointer-events: none`; `.is-opaque` `pointer-events: auto`.
3. **cache-bust `wow153`**, tests, this claim.

## Out of scope

Push / recycle / events scroll / trees (#55). Leave Builder Loop-2 dirty unstaged.

## Roles only

Builder / wall-ui / Operator / Validator.
