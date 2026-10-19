# CLAIM wall-ui-lazy-root-absolute-wow177

## Lock

Under Nest path URL `/projects|stations|roles/...`, relative lazy loads resolve against the path URL (`/projects/mail/mail.js` -> 404). Load domain JS/CSS from site root (`/mail/mail.js`). Guard nest path **writes** until Hub SPA fallthrough (LOOP2): keep `?projects=`; helpers still parse path if present. Local tip only; no push / pack / PyPI / Hub middleware SPA.

## What landed

1. **`lib/lazy.js`** - DOMAINS hrefs root-absolute (`/mail|/score|/todo`); mail bust `?v=wow177`.
2. **`shell-early.js`** - `/lib/perf.js`; **`boot.js`** pack ladder `/packs/...`; **`NEST_PATH_WRITE=false`** guards `compatNestQueryToPath` / `applyFilterToUrl` / `applyRailNestUrl`.
3. **`board.html`** - inert domain seams + floor + `boot.js?v=wow177` / `board.css?v=wow177`.
4. **`wall_logic/domains.py`** - `domain_script_src` returns `/{domain}/{domain}.js`.
5. **Tests** - nest guard + absolute lazy/domain pins; cache-bust tip wow177.

## Glance

1. Recycle mill-wall / hard-refresh from `/` so `boot.js?v=wow177` + lazy tip load.
2. Open mail/score/todo tabs - Network shows `/mail/mail.js` (not `/projects/mail/...`).
3. Project rail/filter keeps `/?projects=<slug>` (not `/projects/<slug>`) until LOOP2 Hub serve.

## Successor

wow178 enables NEST_PATH_WRITE after Hub SPA fallthrough. See CLAIM-wall-ui-nest-path-write-wow178.md.
