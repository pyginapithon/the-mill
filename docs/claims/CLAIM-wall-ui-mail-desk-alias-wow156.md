# Claim - Wall MAIL desk match PROJ:role↔bare + star srcs (wow156)

Status: **local WIP** on `claim/floor-v1-parts`. Committed locally only. Not pushed. No mill-wall recycle (Operator).

## Lock

Glass GRAPH/LIST dst rail may select `PROJ_<slug>:<role>` while lean `mail_tos` store bare `deskId` (e.g. `builder`). `mailDeskMatches` / `mail_desk_matches` must alias both forms so `mailSrcsForDst` is not empty ("no senders for this dst").

Secondary: `mailIsFloor` treats legacy `dst="*"` as floor; `mailSrcsForDst` must still return srcs when `want === "*"`.

Humans remain read-only on Wall. No Loop-2 `/api` contract changes.

## What landed

1. **`mail/mail.js`** - `mailDeskMatches` aliases `PROJ_*:role` ↔ bare deskId; `mailSrcsForDst` allows `want === "*"` despite floor skip.
2. **`wall_logic/mail.py`** - SoR mirror of the same rules.
3. **`tests/wall/test_mail_rules.py`** - PROJ_the-mill:builder -> srcs; `*` -> srcs.
4. **`board.html`** - `mail/mail.js?v=wow156` cachebust (boot stays wow155).
5. **This claim**.

## Glance (host)

1. Recycle mill-wall so it serves this checkout (or confirm `MILL_WALL_SRC=git` already points here) - **Operator**; wall-ui does not restart.
2. Hard-refresh Wall (`mail/mail.js?v=wow156`).
3. MAIL GRAPH: select a `PROJ_*:role` dst that has lean mail_tos with bare role - src rail should list senders (not "no senders for this dst").
4. Select dst `*` - src rail should list star cast senders.

## Out of scope

- Push / mill-wall recycle / pack / PyPI / Playwright
- Loop-2 `/api` contracts
- Mass bump boot.js wow155 -> wow156

## Roles only

Commits / docs / todos use Builder / wall-ui / Operator / Validator - no personal names or home paths.
