# CLAIM wall-ui-nest-path-write-wow178

## Lock

Hub SPA fallthrough for /projects|/stations|/roles is live (Host recycle; GET /projects/finance and /stations/192.0.2.10 return 200 board HTML). Flip glass **NEST_PATH_WRITE=true** so writers emit nest path families again. Preserve **tab in path family + #subtab (or strip tab) in hash** per Host. Local tip only; no push / pack / PyPI.

## What landed

1. **oot.js** - NEST_PATH_WRITE = true (wow178). compatNestQueryToPath / pplyFilterToUrl / pplyRailNestUrl write /projects|<slug>, /stations/<slug>, /roles/<slug>; location.hash kept (#session, #leases, #mail, ...).
2. **oard.html** / **lib/lazy.js** - cache bust ?v=wow178 (boot, board.css, mail).
3. **Tests** - nest write-enabled pin + tip wow178.
4. **This claim**; LOOP2 Hub serve prerequisite satisfied.

## Host URL shape (path + hash)

| Nest | Path | Hash (tab / subtab) |
|------|------|---------------------|
| Project | /projects/finance | #session (strip) or #leases / #watch (session subtab) |
| Station | /stations/192.0.2.10 | #session / #leases |
| Role | /roles/builder | #mail / #jobs |

Deep link example: https://192.0.2.10/projects/finance#session

## Glance

1. Recycle mill-wall / hard-refresh so oot.js?v=wow178 loads.
2. Open / then pick project finance (or cold open /projects/finance#session) - URL stays path family + hash; no ?projects=.
3. Rail station -> /stations/<ip>#...; role -> /roles/<name>#....
4. Hard refresh on nest path still 200 board (Hub SPA).

## Out of scope

- Push / pack / PyPI
- Hub middleware edits (Builder; already live)
