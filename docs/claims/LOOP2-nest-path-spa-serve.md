# Loop-2 - Nest path SPA serve (`/projects|/stations|/roles`)

**From:** Wall (glass wow175)  
**To:** Builder (Hub / mill-wall static)  
**Host GO context:** Nest URLs rewrite to path families; glass-only landed; Hub must not 404 deep links.

## Gap

`agent_coord/server/middleware.py` serves Nest `board.html` only for:

- `/`
- `/board`
- `/index.html`
- `/welcome`

Unknown paths fall through static basename lookup then **404**. Nginx wall edge `location /` proxies to mill-wall (no `try_files` SPA fallback).

After wow175 glass, in-session `pushState`/`replaceState` uses:

- `/projects/<slug>`
- `/stations/<slug>` (IPv4 e.g. `/stations/192.0.2.10` - dots are one path segment)
- `/roles/<slug>`

**Hard refresh or cold open of those paths 404s** until Hub serves board for them.

## Ask (smallest Hub change)

Serve the same Nest board HTML for path prefixes:

- `/projects` and `/projects/*`
- `/stations` and `/stations/*`
- `/roles` and `/roles/*`

(Equivalent: SPA fallback - any non-`/api/*` non-static path returns board.)

Do **not** break relative asset URLs on deep links: either keep serving board only after glass already loaded from `/` (insufficient for cold open), or ensure assets resolve from root (absolute `/boot.js` / `<base href="/">` carefully - hash tabs - **prefer absolute root asset hrefs** or Hub rewrite). Relative `src="boot.js"` under `/projects/finance` would request `/projects/boot.js` today.

## Glass already done (wow175)

- Client writes path; accepts old `?projects=` / `?stations=`|`?lan=` / `?roles=`|`?role=` with compat `replaceState`.
- Station encode: `encodeURIComponent` (dots literal).

## Not this note

Wall pack / PyPI / push. Floor API `lan=` / `project=` contracts unchanged.

## Status (wow178)

Host recycled; Hub serves nest path prefixes (200 board). Glass NEST_PATH_WRITE=true in wow178.
