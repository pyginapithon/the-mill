# Claim - Wall UI parts=events infinite scroll (wow154)

Status: **local WIP** on `claim/floor-v1-parts`. Committed locally only. Not pushed. No mill-wall recycle (Operator).

Parent: wow153 floor-scroll (`c4bb769`) + Builder events `next` fix (`097af3c`).

## Lock

| Item | Lock |
|------|------|
| `parts=events` | First page `?limit=50`; near-bottom `?cursor=` append (dedupe `type:id`) |
| Scroll hosts | `#wire` (Wire body) + `#wire-log` when SESSION History is on (`activity-or-events`) |
| Keep | wow146-153 paint locks; other floor/activity scroll panes |

## What landed

1. **`boot.js`** - enable events in list-next kinds/append/paint/wire; remove wow153 SKIP.
2. **cache-bust `wow154`**, tests, this claim.

## Out of scope

Push / trees (#55). Leave Builder Loop-2 dirty unstaged.

## Roles only

Builder / wall-ui / Operator / Validator.
