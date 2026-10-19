# WALL-CONTRACT - trust browse vs membership (rooms)

Status: Builder SoR on `claim/floor-v1-parts`. Glass separate.
Date: 2026-09-27 PT.
Parent: CLAIM-trust-wall-browse.md

## Matrix

| trust | Wall rooms list | Agent mail-thread |
|-------|-----------------|-------------------|
| limited | membership (room cast) when `?desk=` | room cast |
| high | browse book (no desk filter) | room cast |
| Admin | everything | everything |

## Request hook

```
GET /api/v1/rooms?project=<slug>
GET /api/v1/rooms?project=<slug>&desk=<deskId>          # limited filter
GET /api/v1/rooms?project=<slug>&desk=<deskId>&scope=membership
```

## Response

Every v1 isolate envelope includes `"trust": "high"|"limited"` (from office `mill trust`).

When membership filter applied: `"desk": "<deskId>"`, `"scope": "membership"`, `trees` = room roots whose root cast includes desk.

## wall-ui must wire

1. Read `trust` from any v1/floor payload (or `mill trust`).
2. If `limited`, append seated desk `?desk=` on `/api/v1/rooms` (membership).
3. If `high`, omit `desk` to browse book (unless forcing membership glance).
4. Admin: no membership filter needed.
5. Agent catch-up stays `mill mail-thread <room> --after <latest_id>`; stash `latest_id` from envelope.
