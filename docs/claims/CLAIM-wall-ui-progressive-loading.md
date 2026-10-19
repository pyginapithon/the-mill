# Claim - Wall UI strip-tab loading indicators (wow142)

Status: **local WIP** on `claim/floor-v1-parts`. Committed locally only. Not pushed.

Parent: wow141 finished chrome (`2d888f5`) + host live lock: strip tabs (SESSION/FLOOR/TODO/SCORE/MAIL) themselves need a loading indicator until that domain paints. Pane-body seeds already existed; strip KPIs did not.

## Lock (host)

Visible loading state on each main strip tab (kpi/strip-nav buttons) while that tab's content is still loading - spinner/hourglass on or beside the tab label, clear when that domain paints. Critical CSS so first paint shows it. `wall_perf` stays opt-in. Humans readonly unchanged. Local only; no push / restart.

## What landed (wow142)

1. **`board.html`** - seed each strip KPI with `kpi-loading` + `data-wall-strip-loading="1"` + compact `.kpi-load` (spin + hourglass). Cache-bust `shell.css?v=wow142`, `boot.js?v=wow142`.
2. **`shell.css` / critical** - `.kpi.kpi-loading .kpi-load` rules so first paint shows the strip spinner before board.css / boot.js. Size gate still 16KB.
3. **`boot.js`** - `wallStripLoadHtml`, sticky `_stripReady`, `wallSyncStripTabLoading`; `strip()` keeps spinner until agents/todos/scores/mail (or pane body) ready, then clears. wall_perf opt-in + WALL_HUMAN_READONLY untouched.
4. **Tests + claims**; prior wow141 cache-bust asserts bumped to wow142.

## Glance (host)

1. Recycle mill-wall so it serves this checkout (or confirm `MILL_WALL_SRC=git`).
2. Hard-refresh Wall (`shell.css?v=wow142`, `boot.js?v=wow142`).
3. First paint: finished chrome; each strip tab (SESSION/FLOOR/TODO/SCORE/MAIL) shows spinner/hourglass beside the label (not only pane-body seeds).
4. As each domain's data (or pane) paints, that strip tab's spinner clears and counts/cues appear.
5. Optional `?wall_perf=1` -> `wallPerfDump()`. Off path stays zero-cost.

## Out of scope

- Push / Playwright / pack / PyPI / mill-wall restart from this agent
- Inventing new API routes
- Fat boot.js inlined into HTML
