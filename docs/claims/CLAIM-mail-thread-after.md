# Claim - mill mail-thread --after (#59 mail-thread-after)

Status: **RC Ready** on claim/floor-v1-parts. Local commit only. Not pushed. Not pack/PyPI.
Parent: threads-mail-tree / lean mail-thread. Mill card **#59** (PROJ_the-mill / aws SoR).
Host GO 2026-09-27: catch-up for long ROOMs without full replay.

## Lock (Host GO 2026-09-27 PT)

| Item | Lock |
|------|------|
| Verb | `mill mail-thread <mail_id> [--after <mail_id>]` |
| Omit --after | full TREE/chain (unchanged) |
| With --after | same TREE envelope; `chain` = msgs with **id > after** |
| Bad/missing after | clear **CoordError** (after not on same TREE/chain) |
| Wall HTTP | **none** this shot - no mail-thread HTTP surface exists; do not invent routes |
| Auth | unchanged Bearer sender-or-recipient |

## Files

- `agent_coord/__main__.py` - `--after` on mail-thread CLI
- `agent_coord/client/outbound/__init__.py` - `_INT` already ships `after` into body
- `agent_coord/server/api/mill/rpc.py` - `_h_mail_thread` filter + CoordError
- `tests/server/records/test_room_reply.py` - after filter / missing / zero
- `tests/client/test_outbound.py` - body_from_args after
- this claim

## Claims with path:lines (Builder)

| Claim | Path |
|-------|------|
| CLI `--after` | agent_coord/__main__.py:288-297 |
| body `after` int | agent_coord/client/outbound/__init__.py:119 + :290-296 |
| Filter id > after; same TREE envelope | agent_coord/server/api/mill/rpc.py:917-939 |
| Missing after CoordError | agent_coord/server/api/mill/rpc.py:935-938 |
| Tests after filter/missing/zero | tests/server/records/test_room_reply.py:361-432 |
| Test CLI body after | tests/client/test_outbound.py:267-280 |
| verbs teach | docs/protocol/verbs.md:82 |

## Validator

1. omit `--after` / `after=0` -> full chain
2. `--after` root id -> only newer msgs; tree/root crumbs kept
3. `--after` not on chain / unknown id -> CoordError mentioning after
4. after last msg -> empty `chain` list (envelope kept)

## Out of scope

Push, pack/PyPI, Wall since/after HTTP, SP change, inbox semantics, wall_ui glass.

## Roles only

Builder / wall-ui / Operator / Validator / Host - no personal names or home paths.

## Mill todos

| id | need_id | Status |
|----|---------|--------|
| 59 | mail-thread-after | **RC Ready** (this shot) |
