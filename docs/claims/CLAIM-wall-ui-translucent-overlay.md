# Claim - Wall UI translucent Checking overlay (wow151)

Status: **superseded locally by wow152** (`CLAIM-wall-ui-overlay-empty-opaque`). Was local WIP on `claim/floor-v1-parts`. Committed locally only. Not pushed. No mill-wall recycle (Operator).

Parent: wow150 reuse-inflight (`478a0d6` / `CLAIM-wall-ui-reuse-inflight`).

## Lock

| Item | Lock |
|------|------|
| Checking spinner | **Translucent / semi-transparent** backdrop - last-good pane content stays **visible underneath** |
| Spinner + label | Still readable (near-opaque chip on `.wall-loading`) |
| Behavior | Keep fp-before-paint / reuse-inflight / absorb / switch-gen / keep-prior |
| Not | Solid opaque cover that hides prior paint |

## What landed

1. **`shell.css`** - `.wall-pane-overlay` uses `color-mix` / rgba ~48% panel (not solid `--panel`); light `backdrop-filter`; `.wall-loading` chip stays readable.
2. **cache-bust `wow151`**, this claim, CSS asserts in tests.

## Glance

1. Recycle mill-wall - **Operator**.
2. Hard-refresh `shell.css?v=wow151`.
3. Flip MAIL/TODO: prior rows visible under Checking; spinner readable.

## Out of scope

Push / recycle / Playwright.

## Roles only

Builder / wall-ui / Operator / Validator.

