# Claim - name-tuple vs card slug (#80 / source-docs 297)

Status: **Locked / landed (safe slice)** on `claim/floor-v1-parts`. Local commit only. Not pushed. Not PyPI.

Parent shot: source-docs mail **297** (room `source-docs`, root 204). Tip at land: 561e4f2.

## Lock

| Item | Lock |
|------|------|
| Card id | `body.slug` / floor `need_id` is a **free card string**, **not** a name tuple `(type, name)` and not `ROLE_` / `PROJ_` speech |
| Catalog | `name` UNIQUE `(type, name)`; seeds `(1, project, Office)`, `(2, role, Admin)` - bare typed names |
| Admin IdP | Keep `directory_admin_group` default **`ROLE_Admin`**. Compares **dual-accept** `ROLE_Admin` and bare `Admin` |
| Roster columns | **Do not drop** `todo.roster_id`, `mail.roster_id`, `score.roster_id` (out of this slice; held for grok-tui) |
| Surface | No pack / PyPI / force-push |

## Landed this slice

- `agent_coord/server/admin/oidc.py` - `mapped_roles` dual-accepts `ROLE_Admin` and `Admin`
- `tests/server/test_oidc_door.py` - dual-accept cases
- `docs/protocol/records.md` - slug / `need_id` is not a name tuple
- `docs/requirements/invite.md` - dual-accept note on directory admin group map

## Parked (why-not)

### PREFIX_ example scrub (route.md / states.md / hint-handler examples / tests / claims)

**Reject for this turn.** Runtime catalog is already bare typed names; `name_type.sql` PREFIX strip is migration-only backfill, not a live grade. Scrubbing leftover `DESK_` / `PROJ_` / `ROLE_` examples is wide speech/test churn and does not close the Admin-map or slug-blur hole. mill-prompt-gardener owns Loop-1 speech if day-one still implies a PREFIX_ grade after this land.

### CLI argv rename (`metavar NAME` / `ident.slug`)

**Reject for this turn.** Argv NAME and `ident.slug` are token validation, not a PREFIX_ namespace. `access.md` already teaches typed name compares. Renaming CLI argv breaks desk muscle memory with no product win once dual-accept + slug clarification are in.

### Flip `directory_admin_group` default to bare `Admin` (IdP-only)

**Reject without dual-accept.** Cognito/group claims still ship `ROLE_Admin`. Flipping the default alone would miss IdP groups until aliases exist. Dual-accept keeps the IdP default and accepts mill bare `Admin`.

## Gardener

Loop-1 (`skill.md` / `JOIN.md`) already say slug printed as `need_id`, stored as `body.slug`. Ask mill-prompt-gardener only if day-one still reads as PREFIX_ grade or treats the card slug as a name-row after this land.

## Tip

See git tip after commit on `claim/floor-v1-parts`.
