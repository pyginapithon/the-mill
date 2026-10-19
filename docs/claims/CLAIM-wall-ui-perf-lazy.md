# Claim - Wall UI perf lazy domains (Wave 2 / Loop-3)

Status: **local WIP** on claim/loop-3-wall-mail-rooms. Committed locally only. Not pushed.

Parent: cloud-mill todo **wall-ui-perf-rebuild** (#40).

## Lock

First paint stays shell.css + async board.css (Wave 1). MAIL/TODO/SCORE domain JS+CSS load on first tab open. Poll pauses when document.hidden; multi-tab debounce via poll leader. Keep slim tab-scoped parts= (no stripNeed regress). Do **not** invent a lean mail-without-bodies parts flag - note for Builder if needed.

## What landed (Wave 2)

1. lib/lazy.js (WALL_UI_LIB_LAZY) - wallLoadScript / wallLoadCss / wallEnsureDomain single-flight.
2. board.html - floor.js eager; mail/score/todo in inert `<template id="wall-lazy-domains">`; lib/lazy.js wired.
3. default/todo/todo.js + todo.css - WALL_UI_DEFAULT_TODO domain (millTodoCards).
4. Lazy tab CSS: mail/mail.css, todo/todo.css, score/score.css (extracted from board.css; shell.css untouched for first paint).
5. boot.js - showTab + tick await wallEnsureDomain; visibilitychange pause/resume; wallClaimPollLeader multi-tab lock; slim wallParts unchanged.
6. Static gates - lib/check.py + tests/wall/test_wall_ui_perf_lazy.py; domain pack includes todo.

## Evidence (path:lines)

- agent_coord/web/wall_ui/lib/lazy.js:1-94 WALL_UI_LIB_LAZY / ensureDomain:80 / wallEnsureDomain:92
- agent_coord/web/wall_ui/default/board.html:24 shell.css; :653 lib/lazy.js; :656-661 wall-lazy-domains + floor eager
- agent_coord/web/wall_ui/default/todo/todo.js:1-75 WALL_UI_DEFAULT_TODO
- agent_coord/web/wall_ui/default/mail/mail.css:1 WALL_UI_DEFAULT_MAIL_CSS
- agent_coord/web/wall_ui/default/todo/todo.css:1 WALL_UI_DEFAULT_TODO_CSS
- agent_coord/web/wall_ui/default/score/score.css:1 WALL_UI_DEFAULT_SCORE_CSS
- agent_coord/web/wall_ui/default/boot.js:904-932 wallParts slim; :5913 wallClaimPollLeader; :5933 wallStartFloorPoll; :5940 visibilitychange; :5956 tick(force); :5993 document.hidden; :5996 multi-tab leader; :6068-6100 wallEnsureDomain on paint
- tests/wall/test_wall_ui_perf_lazy.py

## Builder note (API)

MAIL tab still ships full letter bodies via existing `parts=mail` / `mail,trees`. A lean mail-without-bodies slice would need a **new** floor parts flag - **STOP**; do not invent here. Hand to Builder if this machine still stalls on MAIL poll bodies.

## Out of scope

- No Playwright; no Wall / mill-wall restart / www deploy.
- No Loop-2 floor.py parts API change.
- Full boot.js pane paint split remains future (domain pure rules + CSS lazy this wave).

## Hold

mill hold --office cloud-mill the-mill agent_coord/web/wall_ui (id 44, DESK_builder) during edit; drop after commit.

## Wave 3 follow-on

See CLAIM-wall-ui-wave3-perf.md - defer libs, GUIDE template, Rooms trees fingerprint skip, no-op mail paint; Builder ask for lean mail-without-bodies parts unchanged.
