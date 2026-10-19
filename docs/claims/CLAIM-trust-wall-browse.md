# Claim - trust matrix Wall browse vs agent verbs (Host GO B)

Status: **local WIP / Ready for Validator** on `claim/floor-v1-parts`. Local commit only. Not pushed. Not pack/PyPI.
Parent: docs/protocol/access.md + docs/requirements/admin.md. Host GO Wall UI perf room (trust matrix).
Date: 2026-09-27 PT.

## Lock

| trust | Wall (human) | Agent verbs |
|-------|--------------|-------------|
| limited | membership only (room cast) | membership only (room cast) |
| high (default) | may browse book | membership-scoped |
| Admin (`ROLE_Admin`) | everything | everything |

Roles only - no personal names / home paths.

## Smallest SoR shipped

1. **Agent** `mail-thread` sync = room cast (root) + Admin bypass - see CLAIM-mail-thread-cursor-latest.md.
2. **Wall** `GET /api/v1/rooms` (+ other v1 envelopes): stamp top-level **`trust`** (`high`|`limited`).
3. **Hook** for limited filter: `?desk=<deskId>` and/or `?scope=membership` -> `v1_rooms` / `build_rooms(membership_desk=...)` keeps roots whose room cast includes desk. Admin desk => no filter. high without scope => browse book.
4. Documented in `docs/protocol/access.md` (Wall browse vs agent verbs).

## Remaining glass (wall-ui)

- When office `trust=limited`, pass seated human desk as `?desk=` on rooms (and later tree-mail / mailbox if needed).
- When `trust=high`, omit desk filter (browse book) unless product wants explicit `scope=membership`.
- Admin glass: omit filter (or pass Admin desk - Builder already bypasses).
- Do not invent personal names/home paths.

## Files

- `agent_coord/server/records/floor.py` - `_v1_envelope` trust; `_room_root_cast_desks`; `build_rooms(membership_desk=)`; `v1_rooms(desk=, scope=)`
- `agent_coord/server/middleware.py` - pass `?desk=` / `?scope=` into `v1_rooms`
- `docs/protocol/access.md` - matrix
- `tests/server/test_floor_v1_parts.py` - trust stamp + membership filter unit
- this claim + `docs/claims/WALL-CONTRACT-trust-wall-browse.md`

## Claims with path:lines (Builder)

| Claim | Path |
|-------|------|
| Envelope trust stamp | agent_coord/server/records/floor.py:1313 |
| room cast helper | agent_coord/server/records/floor.py:1581 |
| build_rooms membership_desk | agent_coord/server/records/floor.py:1605 |
| v1_rooms desk/scope gate | agent_coord/server/records/floor.py:1648 |
| middleware ?desk/?scope | agent_coord/server/middleware.py:1394 |
| access.md matrix | docs/protocol/access.md (Wall browse vs agent verbs) |
| Test trust stamp | tests/server/test_floor_v1_parts.py:312 |
| Test membership filter | tests/server/test_floor_v1_parts.py:315 |
| Agent room-cast | CLAIM-mail-thread-cursor-latest.md |

## Out of scope

Full Wall ACL rewrite, glass cookie wiring, pack/PyPI, push, other v1 parts membership filter (note for follow).

## Roles only

Builder / wall-ui / Validator / Host / Operator.
