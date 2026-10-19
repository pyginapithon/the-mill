# Claim - Wall UI theme Auto follows system (wow164)

Status: **local WIP** on `claim/floor-v1-parts`. Committed locally only. Not pushed. Not pack/PyPI. No Playwright.

Parent tip: wow163 glass map/timeline consume.

## Roles only

No personal identifiers in commits, Claims, or docs - roles only (host, desk, human, agent, ROLE_Admin, PROJ_Office).

## Lock

Fix Wall THEME Auto so it follows OS `prefers-color-scheme` (live). Light/Dark stay forced. Persist `factory-theme`. Glass only. No push / pack / PyPI / Playwright. Leave OIDC/admin/build-tui WIP unstaged.

## Root cause

Auto left `data-theme="auto"` and relied on CSS `@media (prefers-color-scheme: light)` only (dark = bare `:root`). Light palette also keyed off `html[data-theme-pref="auto"]` alone. No `matchMedia` listener, so Auto did not resolve to `light|dark` and OS theme changes did not re-assert the attribute. On Windows this read as Auto always light.

## What landed

1. **`shell-early.js`** - FOUC: resolve Auto via `matchMedia('(prefers-color-scheme: dark)')`; `data-theme-pref` = choice, `data-theme` = resolved.
2. **`boot.js`** - `wireThemePref` + `wallPreserveThemeChrome` same resolve; `change` listener re-applies when OS theme flips and pref is Auto.
3. **`theme.css` / `board.css`** - palette keys off `data-theme=light|dark` only; Auto media queries are no-JS fallback; removed `data-theme-pref` light selector.
4. **`board.html`** - cache-bust `boot.js` / `shell-early.js` / `theme.css` / `board.css` `?v=wow164`.
5. **Tests** - `test_wall_ui_theme_auto.py` + cache-bust wow164.
6. **This claim**.

## Evidence (path:lines)

- Early resolve: `agent_coord/web/wall_ui/default/shell-early.js` (theme kind, matchMedia)
- Wire + listener: `agent_coord/web/wall_ui/default/boot.js` `wireThemePref`
- Preserve: `agent_coord/web/wall_ui/default/boot.js` `wallPreserveThemeChrome`
- CSS: `agent_coord/web/wall_ui/lib/theme.css` + `default/board.css` (`html[data-theme="light"|"dark"]`)
- Cache-bust: `board.html` `?v=wow164`
- Tests: `tests/wall/test_wall_ui_theme_auto.py`

## Glance (host / Operator)

1. Hard-refresh Wall (`boot.js?v=wow164`).
2. More -> THEME -> **auto**.
3. Set OS / Windows app mode to **Dark** -> Wall goes dark (no reload).
4. Set OS to **Light** -> Wall goes light.
5. THEME **dark** / **light** still force that mode (OS ignored).
6. Reload keeps the last THEME choice (`factory-theme`).

## Out of scope

- Push / pack / PyPI / Playwright / mill-wall recycle (host)
- OIDC / admin / build-tui WIP
- Cut 6 DB css_vars theme knobs
