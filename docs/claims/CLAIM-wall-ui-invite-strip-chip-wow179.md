# CLAIM wall-ui-invite-strip-chip-wow179

## Bug / ask
Host: **Invite Agent** lived in an awkward floating box under the Nest chrome strip
(sibling of `#strip`), not matching strip tab/kpi chips (SESSION / FLOOR / MAIL...).

Also: show invite **count** on the chip - Builder list API not ready -> ship **TBD** badge;
wire real count later (Claim / Loop-2).

## Fix (local tip; no push)
1. Move `#wall-invite-box` **inside** `#strip` as `kpi strip-nav wall-invite-kpi`.
2. Label **INVITE** + `<b id="wall-invite-count">TBD</b>` (title: Invite count TBD until Builder API).
3. CSS: strip chip styling; gate with `[hidden]` only - do **not** use `.on` (that means selected strip tab).
4. Click still `#wall-invite-open` -> `wallInviteOpenFromStrip` -> Nest welcome overlay (wow175 path unchanged).
5. Cache bust `?v=wow179` (board.html, board.css, boot.js, mail, lazy.js). Marker `WALL_INVITE_STRIP_CHIP_WOW179`.

## Glance (host)
Hard-refresh Wall (`boot.js?v=wow179` + `board.css?v=wow179`).
Invite Agent appears as a strip chip next to MAIL with **TBD** count (when trust/admin gate on).
Click -> `#wall-welcome` Nest overlay (not `/welcome` navigate).

## Out of scope
Push / pack / PyPI. Real invite list/count API (Builder). Loop-2 mint list.
