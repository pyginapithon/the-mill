# Claim - mill ROOM agent UX (tree handle + catch-up + reply cast)

Status: **RC Ready (local tip)** on claim/floor-v1-parts. Local commit only. Not pushed. Not pack/PyPI.
Live cloud-mill Hub: **numeric root_id + reply cast PASS**; `--after` filter + TREE/room-name resolve need Hub update (same tip). Wall glass out of scope. build-tui dirt left alone. Async wake parked (Host).

Parent: threads-mail-tree / #59 mail-thread-after. Host GO fan-out 2026-09-27 PT via Gardener.

## Lock (Host GO 2026-09-27 PT)

| Item | Lock |
|------|------|
| Room handle | **TREE name = room name** (Host names). Agents day-to-day use that handle (not only root mail id). |
| Todo handle | TREE name = plan/nest name (same shape; not this shot). |
| Read | `mill mail-thread <mail_id\|TREE/room name> [--after <mail_id>]` |
| Write | `mill reply <mail_id> <body>` on intended node; room cast preserved; no new multi-send for same room chatter |
| Cast delta | `--add-to` / `--remove-to` only when membership changes |
| Inbox crumbs | lean rows carry `tree` + `root_id` (stable handles) |
| Async wake | parked |
| Wall HTTP / glass | none this shot |

## Dogfood (cloud-mill / DESK_builder / ROOM #74 TREE_8d275a0ac1)

Evidence: `~/.mill/evidence/room-agent-ux-20260927/`

| Step | Result |
|------|--------|
| `mill connect the-mill builder --office cloud-mill --vendor grok-bot` | already sitting (bg) |
| `mill inbox` | lean rows show `tree=TREE_8d275a0ac1` + `root_id=74` |
| `mill mail-thread 74` | full chain PASS |
| `mill mail-thread 74 --after N` | CLI+body send `after`; **Hub ignores** (pre-tip) - FILTER live False |
| `mill mail-thread TREE_8d275a0ac1` | CLI accepts; body `tree=`; **Hub: mail_id required** until tip deploy |
| `mill reply 80 --body-file PATH` | **#81** sender=`builder`; mail_tos room cast `{build-mill-shipper,grok-tui,mill-prompt-gardener,validator,wall-ui}`; parent=80 root=74 tree=TREE_8d275a0ac1; no multi-send |

## Files (this shot)

- `agent_coord/__main__.py` - mail-thread argv accepts mail id **or** TREE/room name
- `agent_coord/client/outbound/__init__.py` - digit -> `mail_id` int; else -> `tree`
- `agent_coord/server/api/mill/rpc.py` - `_mail_thread_resolve_mid` (tree -> root mail) + existing `--after` filter
- `tests/server/records/test_room_reply.py` - by-tree / unknown-tree (+ prior after tests)
- `tests/client/test_outbound.py` - tree name + numeric string body
- teach: `docs/protocol/verbs.md`, `docs/protocol/skill.md`, `docs/JOIN.md`
- this claim

## Claims with path:lines (Builder)

| Claim | Path |
|-------|------|
| CLI mail id **or** TREE/room name | agent_coord/__main__.py:287-297 |
| body: digit->mail_id / else->tree | agent_coord/client/outbound/__init__.py:290-300 |
| Resolve TREE/room -> root mail | agent_coord/server/api/mill/rpc.py:887-918 |
| mail-thread + --after filter | agent_coord/server/api/mill/rpc.py:921-973 |
| Reply-all cast; add-to/remove-to only | agent_coord/server/api/mill/rpc.py:747-870 |
| Inbox/lean `tree`+`root_id` crumbs | agent_coord/server/records/mail.py:124-132 + :493-502 |
| Tests: after + by-tree + unknown | tests/server/records/test_room_reply.py:361-470 |
| Tests: outbound after + tree + numeric str | tests/client/test_outbound.py:267-310 |
| Teach | docs/protocol/verbs.md:82; skill.md:111; JOIN.md mail-thread line |

## Validator

1. `mail-thread <root_id>` full chain (unchanged)
2. `mail-thread TREE_<name>` / bare name -> same chain + envelope tree/root_id
3. unknown TREE -> CoordError "no mail room named"
4. `--after` on same TREE -> id > after; bad after -> CoordError
5. reply default cast = parent sender U parent mail_tos (exclude self); add/remove only when flags set
6. Live Hub remasure after tip deploy/pack (aws currently lacks tree resolve + after filter)

## Gaps (Loop-2 / Host)

| Gap | Notes |
|-----|-------|
| aws Hub tip deploy | TREE-name resolve + `--after` live False until Hub runs this tip (local pytest 12/12 mail_thread green) |
| Host-named rooms beyond TREE_hex | **done** this tip: `mill send --name` (see CLAIM-host-tree-room-name.md); no live rename verb for #83 |
| Todo plan TREE-name peek | same handle shape; not this shot |

## Out of scope

Push, pack/PyPI, Wall glass, build-tui, async wake, new multi-send for chatter.

## Roles only

Builder / wall-ui / Operator / Validator / Host / Gardener - no personal names or home paths in product Claims body beyond evidence path convention.

## Mill todos

| id | need_id | Status |
|----|---------|--------|
| 60 | room-agent-ux | **RC Ready** local tip; Hub deploy for live TREE/--after |
| 59 | mail-thread-after | prior RC Ready @ 91c00ed (filter code); live Hub still needs tip |
