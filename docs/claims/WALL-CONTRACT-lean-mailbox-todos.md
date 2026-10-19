# WALL-CONTRACT - lean mailbox + todos (list truncate + detail on open)

Status: Builder SoR on `claim/floor-v1-parts` (Loop-2 cold-SQL + lean unpark).
Audience: wall-ui. Date: 2026-09-26 PT.
Evidence: `~/.mill/evidence/builder-cold-sql-quick-20260926/`

## List / poll (truncated)

### GET `/api/v1/mailbox?project=<slug>` (+ optional `&fp=mail:<16hex>`)

Each `mailbox[]` row is `public_mail` with:

| Field | List behavior |
|-------|----------------|
| `body` | at most **256** chars |
| `body_trunc` | present and `true` only when more body remains; omit when full fits |

Empty-on-match `?fp=` unchanged (empty `mailbox` + echoed fp).

### GET `/api/v1/todos?project=<slug>` (+ optional `&fp=todos:<16hex>`)

Each `needs[]` / `issues[]` card:

| Field | List behavior |
|-------|----------------|
| `doing` | at most **256** chars |
| `detail` | at most **256** chars |
| `doing_trunc` | `true` only when doing clipped; omit otherwise |
| `detail_trunc` | `true` only when detail clipped; omit otherwise |
| `progress` | not truncated (short) |

Treat either `*_trunc` as "has more" for open/detail fetch.

## Open / detail (full text)

| Surface | Request | Response key |
|---------|---------|--------------|
| Mail letter | `GET /api/v1/mail/{id}` | `mail` - full `public_mail` (**no** `body_trunc`) |
| Todo card | `GET /api/v1/todo/{id}` | `todo` - full card (**no** `*_trunc`) |

Aliases after rewrite: `/api/mail/{id}`, `/api/todo/{id}`.
Missing id -> **404** with `error` + `mail`/`todo`: null (mill stamp still present).

No `?project=` required on detail (id is global in the office book).

## Wall-ui consume sketch

1. List/poll: keep using `/api/v1/mailbox` and `/api/v1/todos` (already staggered for Rooms).
2. When painting preview: show `body` / `doing`+`detail` as returned.
3. On open (click letter / card): if `body_trunc` or `detail_trunc`/`doing_trunc`, fetch detail route and replace local row; if flags absent, list payload is already full.

## Out of scope

Progressive trees; lean body-on-open for `/api/floor` aggregator is also lean now on list paths (same trunc). Multi-worker / front httpd still parked.

## List paging (limit + cursor)

See `WALL-CONTRACT-v1-limit-cursor.md`.

- `?limit=` default 50; `?cursor=` last row id; response `next` or null.
- Keeps lean trunc flags on page rows. Detail-on-open unchanged.
