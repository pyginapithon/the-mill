# Claim - Wall UI glass consume progressive trees (wow165)

Status: **local WIP** on `claim/floor-v1-parts`. Committed locally only. Not pushed. Not pack/PyPI. No Playwright.

Parent tip: Builder Loop-2 RC progressive trees `#55` @ `3310c1c` (`CLAIM-v1-trees-progressive.md`).
Contract: `docs/claims/WALL-CONTRACT-v1-trees-progressive.md` (wall-ui expand/scroll consume).
Prior: wow145 limit+cursor dense panes; wow163 joined map/timeline; trees were PARKED full-slice.

## Roles only

No personal identifiers in commits, Claims, or docs - roles only (host, desk, human, agent, ROLE_Admin, PROJ_Office).

## Lock

Wire MAIL Rooms + TODO Nest tree panes onto Builder progressive `GET /api/v1/tree-mail` + `GET /api/v1/tree-todo`:
first paint `?limit=50&depth=1`, cursor `next` append, expand `?parent_id=type:id`, node `has_children`.
Sticky down: `/api/floor?parts=trees` (Builder floor progressive sticky follow). Human-readonly GET-only.
Prefer progressive expand over fat full-tree loads. Checking overlay locks unchanged.
No Builder SoR in Wall commits. No push / pack / PyPI / Playwright. Leave OIDC/admin/build-tui WIP unstaged.

## What landed

1. **`boot.js`** - tree-mail/tree-todo in `pageKinds` with `limit=50&depth=1`; remember `next`; `wallMergeTreesForests` / `wallAppendTreesPage`; list-next + sticky `parts=trees`; `wallFetchTreeExpand` parent_id; outline twist `has_children` / `needs-expand`; scroll binds `#jobs-outline` + mail nest; header wow165.
2. **`board.html`** - `boot.js?v=wow165`.
3. **Tests** - `test_wall_ui_trees_progressive_wow165.py`; cache-bust wow165 across wall suite; floor_v1_consume progressive asserts.
4. **This claim**.

## Evidence (path:lines)

- Header: `agent_coord/web/wall_ui/default/boot.js:1495-1506` wow165 progressive trees (+ un-PARK)
- First paint: `boot.js:1680-1696` `pageKinds` tree-mail/tree-todo + `limit=50` + `depth=1`
- Merge next: `boot.js:1604-1607` `out.next_trees` from tree isolates
- Append/merge forests: `boot.js:7862-7898` `wallTreeNodeKey` / `wallMergeTreesForests` / `wallAppendTreesPage`
- Expand fetch: `boot.js:7926-7970` `wallFetchTreeExpand` `parent_id=` + sticky `parts=trees`
- Outline twist: `boot.js:3148-3160` `has_children` / `data-trees-needs-expand`; click `~3290` `wallFetchTreeExpand`
- Cursor next: `boot.js:8043-8090` tree-mail/tree-todo/trees + sticky `parts=trees&cursor=`
- Scroll: `boot.js:8178-8183` `#jobs-outline` tree-todo + `#mail` tree-mail
- Cache-bust: `board.html:692` `boot.js?v=wow165`
- Tests: `tests/wall/test_wall_ui_trees_progressive_wow165.py`

## Glance (host / Operator)

1. Recycle **mill-wall** so checkout serves tip with Builder `#55` progressive routes.
2. Hard-refresh Wall (`boot.js?v=wow165`).
3. MAIL Rooms Network: `/api/v1/tree-mail?project=...&limit=50&depth=1` (not fat omit-query full slice).
4. TODO Nest Network: `/api/v1/tree-todo?project=...&limit=50&depth=1`.
5. Near-bottom outline / nest: if `next` non-null, append `?limit=50&cursor=...`.
6. Twist on `has_children` row with no local kids: `?parent_id=type:id&limit=50`; children splice under parent.
7. Sticky-down / 404: falls back to `/api/floor?parts=mail,trees` or `todos,trees`; tree next uses `parts=trees`.
8. Checking overlay: opaque empty / translucent over last-good; leave/return keep cache; reuse in-flight (unchanged).

## Out of scope

- Push / pack / PyPI / Playwright / mill-wall recycle (host)
- Builder `floor.py` / middleware / floor `parts=trees` progressive (sticky follow)
- Re-fan-out Promise.all agents+mailbox
- Changing mail.js / score.js / shell.css / theme.css cache tags this ship
- OIDC / admin / build-tui WIP

## Mill todos

| id | need_id | Status |
|----|---------|--------|
| 55 | v1-page-trees-progressive | Builder RC Ready; wall-ui glass wow165 consume |
