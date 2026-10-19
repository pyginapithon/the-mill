# Claim - Wall UI MAIL Rooms scroll + sort by recency (wow168)

Status: **local WIP** on claim/floor-v1-parts. Committed locally only. Not pushed. Not pack/PyPI. No Playwright.
Prior: wow167 trust rooms membership.

## Roles only

No personal identifiers in commits, Claims, or docs - roles only (host, desk, human, agent).

## Lock

1. **Scroll:** `.mail-browser` CSS grid columns lacked `min-height:0`, so overflow-y on `.mail-col` never clipped; global `* { scrollbar-width: none }` hid scrollbars. Fix height chain + rooms-only thin scrollbars.
2. **Sort:** Host wants rooms list sorted by recency (not filtered). Strengthen `mailRoomLatestAt`: mailbox `created`/`at` via `mailAt` when present; else max mail node id as zero-padded 16-digit string. Tie-break higher max mail id before label. Show short recency hint in `.room-meta` when clock present.

Human-readonly GET-only. No push / pack / PyPI / Playwright. No mill core/server.

## What landed

1. **mail/mail.css** - `.mail-browser` height:100%/min-height:0/overflow:hidden; `.mail-col`/`.mail-msg-col` min-height:0 + overflow-y; rooms thin scrollbars.
2. **mail/mail.js** - `mailRoomMaxMailId`; `mailRoomLatestAt` id fallback; sort tie-break.
3. **boot.js** - paintMailRooms / mailRoomsColHtml recency hint + maxMailId tie-break; wow168 header.
4. **board.css** - `.body` min-height:0 (sibling flex-scroll audit).
5. **board.html** / **lib/lazy.js** - `boot.js?v=wow168`, `mail/*?v=wow168`.
6. **Tests** - cache-bust pin flips wow167 -> wow168.
7. **This claim**.

## Audit (other Nest panes)

- TODO kanban / nest: already min-height:0 + overflow-y - OK.
- Score / Floor / Session hist-log / jobs-kanban: already min-height:0 - OK.
- Shell rail: already min-height:0 - OK.
- Sibling fixed this wow: board.css `.body` (flex:1 + overflow-y without min-height:0).
- Follow-up (optional): global scrollbar hide still applies outside Rooms; Host may want thin bars on TODO nest / Floor timeline later.

## Glance (host)

1. Hard-refresh local-mill Wall (`boot.js?v=wow168`).
2. MAIL -> Rooms: left rail + nest scroll via wheel; thin scrollbar visible/draggable.
3. Rooms ordered by latest activity (mailbox clock, else higher mail id); `.room-meta` shows short date/time when clock present.
4. Spot-check tall content on TODO / Floor / Score / Session - scroll should still work.
5. aws Wall still 404 - glass ships on tip for when Wall serves.

## Out of scope

- Push / pack / PyPI / Playwright / mill-wall recycle
- Filtering rooms by recency window (sort only)
- skill.md / mill core

## Tests run

- pytest tests/wall (cache-bust + related)
- python -m agent_coord.web.wall_ui.validate_assets
