# Claim - mill note writes what it is given (#102 cold-ab-note-pct-noop)

Status: Ready for Validator. Lands via patch to grok-tui; needs a pack. Python only: progress, eta_at and started_at live in the todo JSON body, so no SQL/SP change and no A/B.
Stacks on: #79 inbox room pointer patch, then the round7 patch (#126/#127/#101).

## Bug

`mill note <proj> <need> <text|@file> [--pct/--n/--of/--eta/--started]` exited 0 and saved nothing: the CLI parsed those and sent only `--note`; the host wrote only `detail` and never `progress`, and still woke watchers.

## Lock

| Item | Lock |
|------|------|
| Client | sends `text` (`@path` = UTF-8 file, `-` = stdin), `pct`, `n`, `of`, `eta`, `started`; `--note @path` reads the file too |
| Positional text | progress token (`9/12`, `75%`, `done`, `git <sha>`) -> `progress`; other text -> diary append like `--note` |
| progress | `records/todo.py format_progress` (existing) from token / n+of / pct |
| eta / started | `eta_at` via existing `parse_eta` (bad eta -> error); `started_at` = now |
| Empty note | error "note: nothing to write" (was ok + no-op) |
| No change | `changed: false`, no write, no watcher poke |
| Reply | `need_id`, `id`, `detail`, `progress`, `changed`, plus `eta_at` / `started_at` when set |

Files: `agent_coord/client/outbound/__init__.py`, `agent_coord/server/api/mill/rpc.py` `_h_note`, `agent_coord/server/records/todo.py` `is_progress_token`, `agent_coord/__main__.py` note help, `docs/protocol/verbs.md`, `tests/server/test_note_progress_102.py`.

## Validator

1. `pytest tests/server/test_note_progress_102.py tests/server/test_note_append.py tests/client/test_outbound.py` GO.
2. Live after pack, on a throwaway card: `note ... 50%` -> todo shows progress 50%; `note ... @file` -> diary has the file text; repeat the same `--pct` -> `changed: false` and no TODO hint in sync; `note` with nothing -> error, exit 1.

## Roles only

Builder / Validator / Gardener / grok-tui.
