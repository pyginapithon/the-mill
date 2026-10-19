# Claim - Wall UI FLOOR hybrid migrate agents+mail / agents+events to v1 (wow159)

Status: **superseded** by `CLAIM-wall-ui-floor-hybrids-revert-wow160.md` (measure + Builder lock: hybrids back on `/api/floor` until joined Claim). Kept as history. Originally local WIP on `claim/floor-v1-parts`.

Parent tip: `f2315ce` (`wow158: glass consume v1 scores/holds/watchers/events/names`).
Contract base: `docs/claims/WALL-CONTRACT-floor-v1-parts.md` + Builder `_V1_PARTS` (no timeline isolate).
Prior glass: wow157/158 single-part + MAIL/TODO isolates on same branch.

## Lock

Migrate FLOOR multi-part happy paths that have existing v1 isolates off `/api/floor` onto parallel `/api/v1/*` fetches + client merge. Keep sticky `/api/floor` fallback (wow158 pattern). Human-readonly GET-only. No invented Loop-2 endpoints. No Builder SoR in Wall commits. No push / pack / PyPI / Playwright.

## Routes (project scope, v1 up)

| Wall surface | parts= | v1 GETs | notes |
|--------------|--------|---------|-------|
| FLOOR Map | `agents,mail` | `/api/v1/agents` + `/api/v1/mailbox` | Map edges from `floorEdgesFromMailbox` -> mailbox isolate (MAIL surface already uses it) |
| FLOOR Timeline/LAN | `agents,events` | `/api/v1/agents` + `/api/v1/events` | LAN timeline already chose events |
| FLOOR Timeline/project | `agents,timeline` | **PARKED** `/api/floor` | No `/api/v1/timeline` in `_V1_PARTS` / Claim samples |
| SCORE / SESSION / glossary / MAIL / TODO | unchanged | prior wow157/158 | |

Merge: existing `wallMergeV1Isolates` (agents + mailbox->mail + events). Fetch: existing `wallFetchFloorV1` parallel (mailbox+agents has no rooms rail -> Promise.all). Sticky down -> `wallFetchFloorParts` / `/api/floor?parts=`.

## What landed

1. **`boot.js`** - `wallV1Routes` FLOOR hybrids; early absorb includes floor+mailbox; mailbox `fpKinds` key `mail`; header wow159.
2. **`board.html`** - `boot.js?v=wow159`.
3. **Tests** - hybrid migrate + timeline park + cache-bust wow159.
4. **This claim**.

## Evidence (path:lines)

- Header: `agent_coord/web/wall_ui/default/boot.js:1489-1491` (wow159 FLOOR hybrids / timeline PARKED)
- Routes: `boot.js:1549-1564` (`agents,mail` / `agents,events` + park note)
- Early absorb: `boot.js:7251` (`tabNow === "floor"` + `kind === "mailbox"`)
- fp: `boot.js:1654` (`fpKinds.mailbox = "mail"`)
- Cache-bust: `agent_coord/web/wall_ui/default/board.html:692` `boot.js?v=wow159`
- Tests: `tests/wall/test_wall_ui_floor_v1_consume.py`


## Glance (host / Operator)

1. Recycle **mill-wall** so checkout serves this tip (Builder already has agents/mailbox/events isolates).
2. Hard-refresh Wall (`boot.js?v=wow159`).
3. FLOOR Map Network: `/api/v1/agents` + `/api/v1/mailbox` (not `/api/floor` when v1 healthy).
4. FLOOR Timeline with LAN pick: `/api/v1/agents` + `/api/v1/events`.
5. FLOOR Timeline project (no LAN): still `/api/floor?parts=agents,timeline` until Builder ships timeline isolate.
6. Sticky-down / 404: falls back to `/api/floor?parts=...` as before.

## Out of scope

- Push / pack / PyPI / Playwright / mill-wall recycle (host)
- Inventing `/api/v1/timeline`
- Builder `floor.py` / middleware edits in Wall commits
- Changing mail.js / shell.css cache tags this ship

## Blocker for Builder (optional)

`/api/v1/timeline` isolate (+ Claim/sample) would unblock FLOOR Timeline/project hybrid (`agents,timeline`). Not required for Map or Timeline/LAN.
