# CLAIM wall-ui-nest-path-wow175

## Pre-rewrite URL shapes (report)

- **projects:** Nest location used `?projects=<csv>` (e.g. `/?projects=finance#session`). Written by `applyFilterToUrl` / `goFilter` / rail project pick.
- **stations:** **No `?stations=` in the Nest location.** Station (LAN) picks lived only in `sessionStorage` `mill-rail-pick` as `{kind:"lan",id:"<ip-or-host>"}`. Floor scope used internal `lan=<id>` for `/api/floor` - not the browser URL.
- **roles:** **No `?roles=` in the Nest location.** Same `mill-rail-pick` with `{kind:"role",id:"<name>"}`.

## Lock

Rewrite Nest URLs to path families `/projects/<slug>`, `/stations/<slug>`, `/roles/<slug>` (keep hash). Compat: old query (`?projects=` / `?stations=`|`?lan=` / `?roles=`|`?role=`) -> `replaceState` path. Station ids via `encodeURIComponent` (IPv4 dots stay literal so `/stations/192.0.2.10` parses; IPv6 colons `%3A`). Accept path + old query on load. Human-readonly GET-only glass. No Builder SoR / middleware in this Wall commit. No push / pack / PyPI.

## Hub note (Loop-2)

Hub `middleware.py` serves board HTML only for `/`, `/board`, `/index.html`, `/welcome`. **`/projects/*`, `/stations/*`, `/roles/*` currently 404** on hard refresh / deep link (nginx proxies to mill-wall; no SPA catch-all). Glass pushState works after a `/` load. See `docs/claims/LOOP2-nest-path-spa-serve.md`.

## What landed

1. **`boot.js`** - `WALL_NEST_PATH_WOW175` helpers; `currentFilter` / `applyFilterToUrl` / `selectRail` / popstate / rail restore / boot compat redirect.
2. **`board.html`** - `boot.js?v=wow175`.
3. **Tests** - `tests/wall/test_wall_ui_nest_path_wow175.py`.
4. **This claim** + Loop-2 note.

## Glance (host)

1. Recycle mill-wall (or hard-refresh if checkout-served) so `boot.js?v=wow175` loads.
2. Open `http://192.0.2.10/?projects=finance#session` -> URL becomes `/projects/finance#session` (Nest + project).
3. Rail station pick -> `/stations/<ip>` (dots OK). Role pick -> `/roles/<name>`.
4. Deep link `/projects/finance` hard refresh needs Loop-2 Hub SPA serve (until then: load `/` first).

## Out of scope

- Push / pack / PyPI
- Hub middleware SPA serve (Loop-2 Builder)
- Changing floor API `lan=` / `project=` query contracts


## wow178 write enable

Hub SPA fallthrough live. NEST_PATH_WRITE=true (wow178). Writers emit path families; keep hash tab/#subtab. See CLAIM-wall-ui-nest-path-write-wow178.md.

## wow177 guard

NEST_PATH_WRITE=false in boot.js until Hub SPA fallthrough (LOOP2). Writers keep `?projects=`; path helpers still parse. Lazy/domain assets use site-root hrefs (/mail/...). See CLAIM-wall-ui-lazy-root-absolute-wow177.md.
