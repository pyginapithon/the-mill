# CLAIM wall-ui-welcome-invite-nest-wow175

## Bug
Host: Invite Agent strip felt like a full-page welcome replace (Nest not visible),
or no Nest popup in Host's own window while headed PW showed overlay.

Root cause: `board.css` stayed pinned at `?v=wow164` while wow171+ overlay CSS
(translucent backdrop, Nest shows through) lived only in tip `board.css` bytes.
Host browsers kept the wow170 opaque full-screen welcome (`background: rgba(...,0.92)`).
`board.css` also loads async (`media=print` then `all`), so overlay rules could lag.

## Fix (invite/welcome open path only; nest path rewrite untouched)
1. `board.css?v=wow175` cache-bust + z-index 90 (above compose).
2. Sync critical `#wall-welcome` overlay CSS inline in `board.html` (`wall-welcome-critical`).
3. Invite Agent: `wallInviteOpenFromStrip` -> `wallWelcomeShow({ stampQs: true })` only;
   capture-phase delegation; never `location=/welcome`. Optional `?welcome=1` replaceState
   on current Nest path. Marker `WALL_WELCOME_INVITE_NEST_WOW175`.
4. Boot pin already `boot.js?v=wow175` (shared with nest-path WIP).

## Glance (host)
Hard-refresh Wall (must load `board.css?v=wow175` + `boot.js?v=wow175`).
Click **Invite Agent** -> `#wall-welcome` overlay, Nest chrome visible through dim,
URL stays Nest path (`?welcome=1` replaceState ok). Not a leave to `/welcome`.

## Out of scope
Push / pack / PyPI. Nest `/projects|/stations|/roles` path rewrite (other claim).
