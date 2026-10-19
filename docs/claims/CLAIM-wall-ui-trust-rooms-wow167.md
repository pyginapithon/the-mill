# Claim - Wall UI trust rooms membership (wow167)

Status: **local WIP** on claim/floor-v1-parts. Committed locally only. Not pushed. Not pack/PyPI. No Playwright.
Parent tip: Builder trust matrix @ cc417be (CLAIM-trust-wall-browse.md + WALL-CONTRACT-trust-wall-browse.md).
Contract: docs/claims/WALL-CONTRACT-trust-wall-browse.md.
Prior: wow166 nest window chips.

## Roles only

No personal identifiers in commits, Claims, or docs - roles only (host, desk, human, agent, ROLE_Admin, PROJ_Office).

## Lock

Wire Loop-3 wall_ui Nest/MAIL Rooms glass to the Host trust browse matrix:

1. Read 	rust from any v1/floor envelope (wallRememberTrust / wallTrust).
2. If 	rust === limited, append seated desk ?desk=<deskId>&scope=membership on GET /api/v1/rooms.
3. If high, omit desk (browse book).
4. Admin: no membership filter (server is_role_admin bypass when desk passed).
5. Do **not** invent agent mail-thread stash in glass - agent catch-up stays mill CLI.

Seated desk = existing board identity wallResolveDeskId() (URL ?desk/?for, actory-desk-badge, actory-desk / AGENT_COORD_OWNER). No invented login.

Human-readonly GET-only. No Builder SoR in Wall commits. No push / pack / PyPI / Playwright. Leave OIDC/admin/build-tui WIP unstaged.

## What landed

1. **oot.js** - wallRememberTrust / wallTrust / wallRoomsMembershipQuery; rooms fetch appends membership query; trust absorbed from v1 merge + floor slice.
2. **oard.html** - oot.js?v=wow167.
3. **Tests** - 	est_wall_ui_trust_rooms_wow167.py; cache-bust wow167 across wall suite.
4. **This claim**.

## Evidence (path:lines)

- Header: gent_coord/web/wall_ui/default/boot.js:1510 wow167 trust browse note
- Helpers: oot.js:1518 wallRememberTrust; :1526 wallTrust; :1529 wallRoomsMembershipQuery
- Rooms fetch: oot.js:1737-:1738 
oute.kind === "rooms" + wallRoomsMembershipQuery()
- Merge trust: oot.js:1628 meta keys include 	rust; :1631 wallRememberTrust(json)
- Floor absorb: oot.js:2076 mergeFloorSlice trust; :2079 / :2218 remember trust
- Seated desk: oot.js:6876 wallResolveDeskId (URL / badge / factory-desk)
- Cache-bust: oard.html:706 oot.js?v=wow167
- Tests: 	ests/wall/test_wall_ui_trust_rooms_wow167.py
- Contract: docs/claims/WALL-CONTRACT-trust-wall-browse.md

## Glance (host / Operator)

1. Recycle **mill-wall** so checkout serves tip with Builder trust stamp on v1 envelopes (Operator).
2. Hard-refresh Wall (oot.js?v=wow167).
3. Confirm any v1 isolate (e.g. rooms) envelope has "trust":"high"|"limited".
4. With seated desk set (?desk= or actory-desk / badge) and office 	rust=limited: Network GET /api/v1/rooms?...&desk=<id>&scope=membership; rooms list = membership (room cast).
5. With 	rust=high: rooms URL omits desk (browse book).
6. Admin desk: membership filter not applied (server bypass).
7. No desk seated + limited: rooms omit desk; document blocker (no invented login).



## Glance evidence (LAN PT 2026-09-27 ~16:30)

- Live https://192.0.2.10/ serves oot.js?v=wow167 from this checkout (no recycle needed).
- GET /api/v1/rooms?project=Office envelope: "trust":"high", trees=11, no desk/scope.
- Membership hook: GET .../rooms?project=Office&desk=validator&scope=membership -> desk+scope stamped; trees=4 (filtered).
- High + desk only (no scope): trees=11 browse book (server ignores desk when trust=high).
- Office trust currently **high** - limited-office live toggle not performed (would mutate mill trust; Operator).

## Out of scope

- Push / pack / PyPI / Playwright / mill-wall recycle (host)
- Agent mail-thread latest_id stash in glass (mill CLI)
- OIDC / admin / build-tui WIP
- Other v1 parts membership filter (follow)

## Tests run

- pytest tests/wall - 406 passed (incl. 7 in test_wall_ui_trust_rooms_wow167.py)
- node --check boot.js - ok

## Mill todos

| id | need_id | Status |
|----|---------|--------|
| - | trust-wall-browse glass | wall-ui wow167 rooms membership wire |
