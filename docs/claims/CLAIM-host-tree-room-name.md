# Claim - Host TREE room name on mill send (--name)

Status: **local WIP / Ready for Validator** on `claim/floor-v1-parts`. Local commit only. Not pushed. Not pack/PyPI.

Parent: CLAIM-room-agent-ux / Host GO gap (Gardener). Product lock from #60: **TREE name = Host room name**.

## Lock (Host GO update 2026-09-27 PT)

| Item | Lock |
|------|------|
| Multi-To alone | **No** auto room / no `TREE_hex` mint |
| Open room | `mill send --name <room>` stores that room name |
| Omit `--name` | Plain mail (single or multi dest) |
| Read handle | `mill mail-thread <mail_id\|room name>` |
| Conflict | Same room name already a tree -> clear `CoordError` ("already exists") |
| Retrofit live #83 | **No rename verb** - do not raw-SQL aws. Next mint with `--name`; leave `TREE_e8b9eaae75` as-is |

## Files

- `agent_coord/__main__.py` - send `--name ROOM`; help no longer "2+ tos=room"
- `agent_coord/client/outbound/__init__.py` - `name` already in `_STR` (flows CLI -> body)
- `agent_coord/server/api/mill/rpc.py` - `_h_send` gates room on name/tree/room; wraps `tree exists`
- `tests/server/records/test_room_reply.py` - multi no-tree; named Host room; conflict; by room name
- `tests/client/test_mail_cli_shape.py` - body `--name` + help
- teach: `docs/protocol/verbs.md`, `docs/protocol/skill.md`, `docs/JOIN.md`, `.agents/skills/mill-desk/SKILL.md`
- this claim

## Claims with path:lines (Builder)

| Claim | Path |
|-------|------|
| CLI `--name ROOM` | agent_coord/__main__.py:203-210 |
| body `name` wire | agent_coord/client/outbound/__init__.py:104 (`name` in `_STR`) |
| Room mint only when name | agent_coord/server/api/mill/rpc.py:672-695 |
| Conflict -> CoordError | agent_coord/server/api/mill/rpc.py:690 |
| mail-thread room name | agent_coord/server/api/mill/rpc.py:905+slug_tree |
| Tests multi/named/conflict | tests/server/records/test_room_reply.py:73-136 |
| Tests by room name | tests/server/records/test_room_reply.py:483 |
| CLI shape `--name` | tests/client/test_mail_cli_shape.py:257 |
| Teach | docs/protocol/verbs.md send row; skill.md; JOIN.md; .agents/skills/mill-desk/SKILL.md |

## Acceptance (glance)

```text
mill send --name dev-standup-2026-09-27 --body-file open.txt --to-desk builder --to-desk validator
# -> room root TREE_dev-standup-2026-09-27

mill mail-thread dev-standup-2026-09-27
# -> same chain as root mail id

mill send --body-file plain.txt --to-desk builder --to-desk validator
# -> no TREE / room=false
```

## #83 retrofit (aws ROOM TREE_e8b9eaae75)

No mill tree-rename verb. Prefer **next mint** with `--name <room>`. Do not raw-SQL live aws.

## Out of scope

Push, pack/PyPI, Wall glass, build-tui dirt, reply-path hex mint when parent off-tree (unchanged), async wake.

## Roles only

Builder / Validator / Host / Gardener / Operator - no personal names or home paths.
