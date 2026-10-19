# Claim - Wall UI floor part fingerprint glass (Loop-3)

Status: **local WIP** on `claim/loop-3-wall-mail-rooms`. Committed locally only. Not pushed.

Parent: cloud-mill todo **#40** / **wall-ui-perf** (Wave 1-3 on this branch). Builder SoR: `claim/floor-fingerprint` @ `b337b2d` (`mill_fp` + empty-on-match). Contract: Builder evidence `WALL-CONTRACT.md` (also `/workspace/WALL-CONTRACT.md`).

## Lock

Glass consume for floor part fingerprints. No progressive `trees_depth`. No lean mail-without-bodies. Do not edit `floor.py` / mill_fp SQL. Do not apply SQL to lan/aws (Host GO / Builder).

## Contract (consume)

```
GET /api/floor?project=<slug>&parts=mail,trees&fp=mail:<16hex>,trees:<16hex>
```

- Always HTTP 200 (no 304).
- Unchanged part -> empty arrays/objects + echo `fp` map.
- Client stores **only** echoed fps; key by `floorScope().key + "|" + parts`.
- Empty + unchanged fp -> keep prior `window._floor` slice; skip paint for that part.
- Empty + new fp -> real empty (trees wipe allowed).
- `fp` missing (old servers) -> do not paint-skip on empty alone (pre-fp trees keep remains for lan nest wipe).

## What landed

1. **`boot.js` helpers** - `FLOOR_PART_KEYS`, `floorFpScopeKey` / `floorFpStored` / `floorFpRemember` / `floorFpQuery`, `floorPartPayloadEmpty`, `floorPartFpHit`.
2. **Poll** - `_tickBody` appends `&fp=` when stored fps exist for requested parts.
3. **Merge** - `mergeFloorSlice(prev, slice, { storedFp })` keeps prior keys on fp hit; echoes `fp` / `mill` onto the book.
4. **Paint** - `partPaint(name) = sliceHas(name) && !fpHits[name]`; Wave 2/3 hygiene kept (hidden pause, poll leader, slim `parts=`, Rooms trees client sig, chromeOnly).
5. **Cache-bust** - `board.html` `boot.js?v=wow135`.

## Behavior matrix

| Case | Client | Server | Glass |
|------|--------|--------|-------|
| Cold | no stored fp | full + `fp` | take payload; store echoed fp; paint |
| Hit | send `fp=` | empty + same fp | keep prior slice; skip part paint |
| Miss | send `fp=` | full + new fp (or empty + new fp) | take payload; store new fp; paint |
| Old server | may send `fp=` | no `fp` map | take payload; no empty-on-match skip |

## Evidence (path:lines)

- `agent_coord/web/wall_ui/default/boot.js` - `FLOOR_PART_KEYS` / `floorFp*` / `floorPartFpHit` (~1000); `mergeFloorSlice` opts.storedFp; `_tickBody` `fpQ` + `fpHits` + `partPaint` (~6130)
- `agent_coord/web/wall_ui/default/board.html` - `boot.js?v=wow135`
- Tests: `tests/wall/test_wall_ui_floor_fp.py` (+ `test_wall_floor_parts_poll.py` partPaint assert)

## Ready after SQL apply?

**Yes (glass Ready)** when lan/aws hosts have `mill_fp` + floor empty-on-match wire (Builder / Host GO). Until then old-server path still works (no false paint-skip).

Host must: apply Builder SQL / pack on target hosts; hard-refresh Wall (`boot.js?v=wow135`); glance MAIL/Rooms or Jobs poll - Network shows `fp=` after first cold; subsequent polls empty-on-match without DOM thrash.

## Out of scope

- Progressive trees (`trees_depth`)
- Lean mail-without-bodies
- Applying SQL to live lan/aws
- Editing `floor.py` / mill_fp SQL
- Push / pack / PyPI

## Hold

`mill hold` unavailable (no sitting mill connect). Edited carefully under `agent_coord/web/wall_ui` only.
