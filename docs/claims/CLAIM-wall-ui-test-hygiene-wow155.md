# Claim - Wall UI test hygiene + shell budget (wow155)

Status: **local WIP** on `claim/floor-v1-parts`. Local only; not pushed.

Parent: wow154 events-scroll (`0e29a548`).

## What

1. Trim `shell.css` under 16KB Wave-1 gate (keep translucent/opaque overlay).
2. Extract board.html inline theme/hash/perf scripts to `shell-early.js`.
3. Update brittle `/api/floor` fetch literal asserts to `wallFetchFloorParts` / `floorUrl` semantics.
4. No Builder Loop-2 / floor API change.

## Roles only

Builder / wall-ui / Operator / Validator.
