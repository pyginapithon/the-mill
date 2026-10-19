# Claim - Wall UI reuse in-flight fetch on leave/return (wow150)

Status: **superseded locally by wow151** (`CLAIM-wall-ui-translucent-overlay`). Was local WIP on `claim/floor-v1-parts`. Committed locally only. Not pushed. No mill-wall recycle (Operator).

Parent: wow149 absorb-off-pane (`3ae0589` / `CLAIM-wall-ui-absorb-off-pane`).

## Lock

| Item | Lock |
|------|------|
| Leave then return before fetch completes | **Do NOT** start a new DB/API call; reuse the in-flight request |
| UI while waiting | Checking spinner until in-flight settle (wow151: translucent) |
| Same scope + same `wallParts()` | `wallReuseInflightForReturn` clears `_tickAgain` and marks settle to paint LIVE |
| Different parts/tab | Still queues a follow-up tick (parts changed) |
| Keep | wow146-149, limit=50, lean, stagger, wall_perf, human readonly |

## Root cause

`showTab` / subtoggles always bumped switch-gen and called `tick(true)`. With `_tickInflight` set, that only set `_tickAgain`, so the in-flight settle was treated as stale (off-pane absorb) and a **second** fetch started after. Leave->return mid-flight paid for two DB calls and never painted the returned live pane from the first result.

## What landed

1. **`boot.js` (wow150)** - `wallShouldReuseInflight` / `wallReuseInflightForReturn` / `_tickInflightParts`+`Scope`; showTab + mail/jobs/floor/session reuse path; stale settle falls through to live paint when reuse flagged.
2. **cache-bust `wow150`**, tests, this claim.

## Glance

1. Recycle mill-wall - **Operator**.
2. Hard-refresh `boot.js?v=wow150`.
3. Open MAIL, flip away, return before check finishes - one fetch; Checking until it completes; pane paints from that result (no second network for same parts).

## Out of scope

Push / recycle / Playwright.

## Roles only

Builder / wall-ui / Operator / Validator.
