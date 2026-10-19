# Claim - mail-thread catch-up: latest_id + room cast (Host GO A)

Status: **local WIP / Ready for Validator** on `claim/floor-v1-parts`. Local commit only. Not pushed. Not pack/PyPI.
Parent: CLAIM-mail-thread-after / Host GO Wall UI perf room (catch-up polish).
Date: 2026-09-27 PT.

## Lock (Host GO + room flip)

| Item | Lock |
|------|------|
| Catch-up | whole TREE under named room/root with `id > after` (**siblings included**), NOT one reply branch |
| Sync key | **room cast** (root sender U root mail_tos), NOT per-mail mail_tos |
| Omitted reader | Mid-thread reply that omits a root-cast desk still returns for that desk |
| Wire | keep `mill mail-thread <room> --after <id>` |
| **`--cursor`** | **PARKED** (do not add alias) |
| Envelope | always `latest_id` = max id on **full** chain (stable under --after / empty chain) |
| Park also | `--since`, Hub bookmark, any `mill read` verb |
| Agents | membership-scoped (room cast); Admin = everything; no second full-thread verb |
| Wall HTTP | none this shot for mail-thread |

## Files

- `agent_coord/server/api/mill/rpc.py` - root-cast auth + `latest_id` + --after filter
- `agent_coord/__main__.py` - --after help (no --cursor)
- `tests/server/records/test_room_reply.py` - latest_id / siblings / omitted-reader
- teach: `docs/protocol/verbs.md`, `docs/protocol/skill.md`, `docs/JOIN.md`, `.agents/skills/mill-desk/SKILL.md`
- this claim; parent `CLAIM-mail-thread-after.md` still holds --after CoordError cases

## Claims with path:lines (Builder)

| Claim | Path |
|-------|------|
| Root-cast auth + Admin bypass | agent_coord/server/api/mill/rpc.py:965+ / is_role_admin |
| latest_id on envelope | agent_coord/server/api/mill/rpc.py:946 |
| --after catch-up (whole TREE) | agent_coord/server/api/mill/rpc.py:995 |
| CLI --after help (no --cursor) | agent_coord/__main__.py:307 |
| Test latest_id | tests/server/records/test_room_reply.py:484 |
| Test sibling TREE catch-up | tests/server/records/test_room_reply.py:509 |
| Test omitted-reader root cast | tests/server/records/test_room_reply.py:540 |
| Teach | docs/protocol/verbs.md; skill.md; JOIN.md; .agents/skills/mill-desk/SKILL.md |

## Acceptance

1. omit `--after` / after=0 -> full chain + `latest_id`
2. `--after` root -> sibling replies + nested under other branches all present; `latest_id` unchanged
3. after last -> empty `chain`; `latest_id` still max full chain
4. root-cast desk omitted on a mid-thread reply can still `mail-thread` room / that reply id
5. stranger (not root cast, not Admin) refused
6. no `--cursor` flag on CLI

## Out of scope

Push, pack/PyPI, `--cursor`, Wall mail-thread HTTP, glass, build-tui dirt.

## Roles only

Builder / Validator / Host / wall-ui / Operator - no personal names or home paths.
