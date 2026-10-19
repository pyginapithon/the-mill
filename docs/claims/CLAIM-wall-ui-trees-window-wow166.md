# Claim - Wall UI nest window chips (wow166)

Status: **local WIP** on `claim/floor-v1-parts`. Committed locally only. Not pushed. Not pack/PyPI. No Playwright.
Parent tip: Builder Loop-2 RC Ready `#58` @ `c7bc422` (`CLAIM-v1-trees-window.md`).
Contract: `docs/claims/WALL-CONTRACT-v1-trees-window.md` (wall-ui All | 1d | 1w | 30d chips).
Prior: wow165 progressive tree-mail/tree-todo consume.

## Roles only

No personal identifiers in commits, Claims, or docs - roles only (host, desk, human, agent, ROLE_Admin, PROJ_Office).

## Lock

Wire Loop-3 wall_ui Nest filter chips on BOTH surfaces:
- MAIL Rooms / `tree-mail`
- TODO Nest / `tree-todo`

Chips: **1 day / 1 week / 30 days / All**. All = omit `window=`. Pass `?window=` on progressive fetches (`limit` / `cursor` / `depth` / `parent_id` unchanged). Persist pref like other Wall span prefs (`factory-trees-window`). Chip hosts: `#todo-nest-filters` (existing) + `#mail-rooms-filters` (added).

Human-readonly GET-only. No Builder SoR in Wall commits. No push / pack / PyPI / Playwright. Leave OIDC/admin/build-tui WIP unstaged.

## Sticky (v1 down)

Floor `parts=trees` does **not** take `window=` this shot (Builder sticky follow). When `_wallFloorV1Down`:
- sticky fetches omit `window=` (**full trees**)
- chips paint **All-only** (non-All buttons disabled) so the host does not imply a filter that floor cannot apply

## What landed

1. **`board.html`** - `#todo-trees-window` chips inside `#todo-nest-filters`; `#mail-rooms-filters` / `#mail-trees-window` for MAIL Rooms; `boot.js?v=wow166`.
2. **`boot.js`** - `loadTreesWindow` / `setTreesWindow` / `wallTreesWindowQuery`; first-paint + next + expand pass `?window=` on v1 tree routes; sticky All-only; wire + localStorage `factory-trees-window`.
3. **Tests** - `test_wall_ui_trees_window_wow166.py`; cache-bust wow166 across wall suite.
4. **This claim**.

## Evidence (path:lines)

- Header: `agent_coord/web/wall_ui/default/boot.js:1507` wow166 window chips + sticky All-only note
- Pref + chips: `boot.js:2928-3010` TREES_WINDOW_KEY / wallTreesWindowQuery / setTreesWindow / sticky All-only
- First paint: `boot.js:1698-1703` depth=1 + wallTreesWindowQuery()
- Expand: `boot.js:8043-8045` v1 parent_id + window; sticky floor omits window
- Cursor next: `boot.js:8180-8188` v1 next + window; sticky floor omits
- Wire: `boot.js:8870-8890` click hosts + export
- TODO chips: `board.html:278-283` #todo-trees-window in #todo-nest-filters
- MAIL chips: `board.html:360-367` #mail-rooms-filters / #mail-trees-window
- Cache-bust: `board.html:706` boot.js?v=wow166
- Tests: `tests/wall/test_wall_ui_trees_window_wow166.py`

## Glance (host / Operator)

1. Recycle **mill-wall** so checkout serves tip with Builder `#58` window routes (`tree-mail` / `tree-todo` `?window=`).
2. Hard-refresh Wall (`boot.js?v=wow166`).
3. TODO -> Nest: chips **1 day / 1 week / 30 days / All**; Network `GET /api/v1/tree-todo?...&limit=50&depth=1` and with chip `...&window=1d` (All omits `window=`).
4. MAIL -> Rooms: same chips in pane filters; Network `GET /api/v1/tree-mail?...&window=1w` (All omits).
5. Near-bottom / expand still pass `limit`/`cursor`/`parent_id` **and** current `window=` when set.
6. Sticky-down / 404: floor `parts=trees` omits `window=`; chips lock All-only until v1 up.
7. Pref survives reload (`localStorage factory-trees-window`).

## Out of scope

- Push / pack / PyPI / Playwright / mill-wall recycle (host)
- Builder `floor.py` / middleware / floor `parts=trees` window (sticky follow)
- New window tokens beyond `1d|1w|30d`
- OIDC / admin / build-tui WIP

## Mill todos

| id | need_id | Status |
|----|---------|--------|
| 58 | nest-mail-filter-windows | Builder RC Ready @ c7bc422; wall-ui glass wow166 chips |
