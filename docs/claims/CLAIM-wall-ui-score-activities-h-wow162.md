# Claim - Wall UI SCORE chip activities/h (wow162)

Status: **local WIP** on `claim/floor-v1-parts`. Committed locally only. Not pushed. Not pack/PyPI. No Playwright.

Parent tip: Builder Claim score activities/hour (`c3e6648`) on wow161 glass (`959aa3a`). Reads existing floor/v1 scores kpis - no Loop-2 invent.

## Roles only

No personal identifiers in commits, Claims, or docs - roles only (host, desk, human, agent, ROLE_Admin, PROJ_Office).

## Lock

SCORE glass: map KPI `mill-office.activities` -> chip label **activities/h**. Informational (target empty) - non-zero Last must not paint red/fail. Consume existing `/api/v1/scores` / floor kpis path (wow158). Human-readonly. No score_tick / mill core edits. No push / pack / PyPI / Playwright. Do not revert wow160/161.

## What landed

1. **`score/score.js`** - `SCORE_OFFICE_CHIPS` + `SCORE_KPI_LABELS` (`mill-office.activities` -> `activities/h`); `scoreKpiLabel` / `scoreFindKpi`; `kpiMiss` empty/blank target never numeric miss.
2. **`boot.js`** - Office chip strip paints activities/h from any-owner kpi; detail/hot/desk headers use `scoreKpiLabel`.
3. **`wall_logic/score.py`** - SoR mirror: empty/blank target never numeric `kpi_miss`.
4. **Cache-bust wow162** - `board.html` `boot.js?v=wow162` + `score/score.js?v=wow162`; `lib/lazy.js` live domain URL also `?v=wow162`.
5. **Tests** - `tests/wall/test_score_rules.py` empty-target cases + glass label/cache-bust + desk-row miss=0.
6. **This claim**.

## Evidence (path:lines)

- Label map + chips: `agent_coord/web/wall_ui/default/score/score.js:47-73` (`SCORE_OFFICE_CHIPS`, `SCORE_KPI_LABELS`, `scoreKpiLabel`, `scoreFindKpi`)
- Empty-target miss gate (JS): `score/score.js:15-26` (`kpiMiss`)
- Office chip paint: `agent_coord/web/wall_ui/default/boot.js:6340-6359` (`paintScoreOfficeTotals` Office section)
- Label in detail/hot/desk: `boot.js:6306+` / `6320+` / `6367+`
- Empty-target miss gate (SoR): `agent_coord/web/wall_logic/score.py:39-54` (`kpi_miss`)
- Cache-bust: `board.html:654` `score/score.js?v=wow162`; `board.html:692` `boot.js?v=wow162`; `lib/lazy.js:69` live load
- Tests: `tests/wall/test_score_rules.py:56-78` (param empty target); `:335-376` (glass + desk-row)

## Glance (host / Operator)

1. Recycle **mill-wall** so checkout serves this tip (optional if static wall_ui already from checkout).
2. Hard-refresh Wall (`boot.js?v=wow162`, `score/score.js?v=wow162`).
3. Opt-in KPI already minted (Builder): `mill score-add mill-office.activities` + tick - SCORE Office chip shows **activities/h** Last = count; target blank; non-zero is not red.
4. Network SCORE still `/api/v1/scores` (wow158); no new glass invent.

## Out of scope

- Push / pack / PyPI / Playwright / mill-wall recycle (host)
- score_tick / BOOK_SQL / mill core
- Reverting wow160 hybrids or wow161 perf strip
- Loop-2 API invent
