# Claim - Wall instant shell.css (Wave 1 / Loop-3)

Status: **local WIP** on `claim/floor-v1-parts`. Extended in wow140-wow142 (finished chrome + strip-tab loading on first paint). Committed locally only. Not pushed.

Parent: cloud-mill todo **wall-ui-perf-rebuild** (#40).

## Lock

First paint must not wait on fat board.css (~124KB) or block on large boot.js. Keep tab-scoped parts= slim poll (no stripNeed fat default regress).

## What landed (Wave 1)

1. default/shell.css - critical chrome (WALL_UI_DEFAULT_SHELL_CSS + WALL_UI_SHELL_CRITICAL wow142): body/#shell/#rail grid columns/header/strip/subnav + main/.pane.on/pane-body flex children/mail/todo/floor skeleton + fixed filter/help overlays. Full look stays in board.css. Gate 16KB.
2. board.html - load order: theme.css (blocking) then shell.css (blocking) then board.css async (media=print + onload) + noscript fallback. boot.js gets defer + cache bump.
3. Slim poll unchanged - wallParts() still returns tab core only; no stripNeed concat.
4. Static gates - lib/check.py validates shell.css when present; tests/wall/test_wall_ui_shell_css.py + existing test_wall_floor_parts_poll.py.

## Evidence (path:lines)

- agent_coord/web/wall_ui/default/shell.css:1 (marker WALL_UI_DEFAULT_SHELL_CSS)
- agent_coord/web/wall_ui/default/board.html:22-26 theme/shell/async board.css
- agent_coord/web/wall_ui/default/board.html:687 script defer boot.js
- agent_coord/web/wall_ui/default/boot.js:890-918 wallParts return core (unchanged slim)
- agent_coord/web/wall_ui/lib/check.py:233-245 shell.css gate
- Tests: tests/wall/test_wall_ui_shell_css.py, tests/wall/test_wall_floor_parts_poll.py

## Out of scope / not done

- No Playwright; no Wall restart / www deploy (Host asks).
- No pane lazy-split of boot.js; no Loop-2 floor API change.
- LCP remasure = Validator after live serve of this shell.

## Hold

mill hold --office cloud-mill the-mill agent_coord/web/wall_ui (id 43, DESK_builder) during edit; drop after commit.

