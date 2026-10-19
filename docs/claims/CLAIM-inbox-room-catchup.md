# Claim - inbox room catch-up cold-desk UX (#79)

Status: STALE on mark semantics. Current rule: a fetch does not stamp; reply marks the parent; `mark` marks the rest; `--mark` / `--no-mark` are accepted and do nothing (#195). Rows below that say otherwise are history.

Original status: shot 1 (help) shipped on main 94db551. Shot 2 (inbox `rooms` pointer) Ready for Validator; lands via patch, needs a pack.
Parent: Loop-1 speech (mail-thread teach in skill/verbs/JOIN) + Host lock room traffic = TREE.

## Locked acceptance (card #79 + Host lock)

| Item | Lock |
|------|------|
| Room traffic | TREE only |
| Cold desk room catch-up | Prefer `mail-thread <id\|TREE-or-room-name> [--after <id>]` |
| Plain `inbox` | Desk unread; a fetch does not stamp; **not** room catch-up |
| Desk catch-up | `inbox --all` and/or `--after <id>` (desk list; still not room TREE) |
| Inbox mark-read semantics | **unchanged** this shot |
| Wall / sync envelope redesign | **out of scope** |

## Software this shot (smallest UX)

Harden CLI help so cold desks cannot miss the mail-thread path. Loop-1 docs already teach the same.

## Files

- `agent_coord/__main__.py` - inbox / mail-thread help strings
- `tests/client/test_inbox_room_catchup_help.py` - help steers to mail-thread; cp1252
- this claim

## Validator

1. `mill inbox --help` mentions mail-thread / Not room catch-up; `--after` has help
2. `mill mail-thread --help` names room catch-up + `--after`
3. `pytest tests/client/test_inbox_room_catchup_help.py` GO
4. No change to inbox mark-read default

## Out of scope

Push, pack/PyPI, Wall HTTP, inbox mark-read flip, new listing verb, sync envelope redesign.

## Roles only

Builder / Validator / Host / Gardener - no personal names or home paths.

## Shot 2 - inbox names the room catch-up (#79 software)

Help text alone does not reach a cold desk that never reads `--help`. Smallest software fix: the CLI inbox reply carries a pointer per room.

| Item | Lock |
|------|------|
| Where | Client only: `agent_coord/client/http.py` `inbox_room_pointers` + `mill_http_from_args` |
| Shape | envelope key `rooms`: `[{"tree", "root_id", "letters", "catch_up": "mill mail-thread <root_id>"}]`, sorted by root_id, one row per TREE on this page |
| When | `inbox` verb, `ok` true, at least one letter with `tree` + `root_id` (crumbs the Hub already returns). Absent otherwise |
| `--raw` | unchanged (no `rooms`) |
| Mark-read | unchanged. No SQL, no SP, no Hub change, no extra call |

Files: `agent_coord/client/http.py`, `agent_coord/__main__.py` (inbox description), `docs/protocol/sync.md` (What the command prints), `docs/protocol/verbs.md` (inbox row), `tests/client/test_inbox_room_pointers.py`, this claim.

### Validator

1. `pytest tests/client/test_inbox_room_pointers.py` GO (pointers grouped + sorted, off-tree skipped, envelope keeps result/sync, reply not mutated, `--raw` and other verbs unchanged).
2. Live after pack: cold desk with an unread room letter runs `mill inbox`; reply has `rooms[].catch_up`; running it shows the earlier room letters.
3. Inbox with no TREE letters: no `rooms` key.
