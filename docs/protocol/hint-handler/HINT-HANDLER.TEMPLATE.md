# HINT-HANDLER template

Copy into a **task-local** program. Arm it with `mill route add`. `--owner` goes before the key. Call `parse_stdin()` with no argument.

## Contract (from protocol docs - do not invent)

| Item | Rule |
| :--- | :--- |
| stdin | One JSON object: HINT frame `{type,id,hint,detail?}` (+ optional `desk`/`route` stamps) |
| route_key | `f"{type}:{hint}"` e.g. `mail:MAIL`, `todo:TODO` |
| detail | This desk's `watcher.hint`, or cheap default when NULL (hints.md) |
| mill-fetch | Leftovers only - MAIL->`mill inbox`; TODO->that card (no full board dump) |
| exit | **0** after STOP - mill connect does **not** mill-update for exit 0 (connect.md) |
| ignore | `heartbeat:PING`, `join:JOIN` -> exit 0 |

Copy `examples/stub_handler.py`. Do not keep a second skeleton here.

The stub sets its import root to `parents[1]`, which is `docs/protocol/hint-handler` only while the file stays in `examples/`. A task-local copy must set that root to `docs/protocol/hint-handler` or `tools.hint_handler` does not import.

mill connect discards stdout and stderr. The stub appends `hint-evidence.jsonl` beside the program. Replace that write with your task verbs. `mill send` / `mill label-add` / `mill label-remove` each append a line while the route is still armed.

## Arm

```text
mill route add --owner <desk> mail:MAIL -- python path/to/on_mail.py
mill route add --owner <desk> todo:TODO -- python path/to/on_todo.py
mill route add --owner <desk> * -- python path/to/desk_handler.py
```

Then `mill connect` up, then `mill add <type>:<id> --hint "field,names"` on that activity. A later write is the trigger.

## Drop

```text
mill route rm --owner <desk> mail:MAIL
mill route rm --owner <desk> todo:TODO
```

Stop mill connect when the collab ends.
