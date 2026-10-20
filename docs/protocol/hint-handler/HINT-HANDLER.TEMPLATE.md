# HINT-HANDLER template

Copy into a **task-local** program. Arm it with `mill route add` from the same parent shell that started `mill connect`. Call `parse_stdin()` with no argument.

## Contract (from protocol docs - do not invent)

| Item | Rule |
| :--- | :--- |
| stdin | One JSON object. Watcher frame `{type,id,hint,detail?}` (+ optional `desk`/`route`). A letter is `{id,idem,kind,desk}` with `kind` `mail` |
| route_key | `type:hint` (for example `todo:TODO`), or `mail:MAIL` for `{kind: mail}` |
| detail | This desk's `watcher.hint`, or cheap default when NULL (hints.md). A letter has no detail |
| mill-fetch | Leftovers only - MAIL->`mill inbox`; TODO->that card (no full board dump) |
| exit | **0** after STOP - mill connect does **not** mill-update for exit 0 (connect.md) |
| stdout | Read by mill connect. Last line `not-mine` means next. Any other exit 0 is handled. stderr is discarded |
| ignore | `heartbeat:PING`, `join:JOIN` -> exit 0 |

Copy `examples/stub_handler.py`. Do not keep a second skeleton here.

The stub sets its import root to `parents[1]`, which is `docs/protocol/hint-handler` only while the file stays in `examples/`. A task-local copy must set that root to `docs/protocol/hint-handler` or `tools.hint_handler` does not import.

A print is not evidence. The stub appends `hint-evidence.jsonl` beside the program. Replace that write with your task verbs. `mill send` pushes the letter. `mill label` / `mill unlabel` on a watched todo, join, hold, or score are a later write. A mail label does not push another letter.

## Arm

The desk is the sitting connect. Same parent shell as connect:

```text
bash -c 'mill connect <desk> >/dev/null 2>&1 & trap "kill $!" EXIT; mill route add mail:MAIL -- python path/to/on_mail.py'
bash -c 'mill connect <desk> >/dev/null 2>&1 & trap "kill $!" EXIT; mill route add todo:TODO -- python path/to/on_todo.py'
bash -c 'mill connect <desk> >/dev/null 2>&1 & trap "kill $!" EXIT; mill route add * -- python path/to/desk_handler.py'
```

Then keep `mill connect` up, then `mill add <type>:<id> --hint "field,names"` on that activity (same shell). A later write is the trigger. Mail has no watcher; `mill send` is the trigger.

## Drop

```text
bash -c 'mill connect <desk> >/dev/null 2>&1 & trap "kill $!" EXIT; mill route rm mail:MAIL'
bash -c 'mill connect <desk> >/dev/null 2>&1 & trap "kill $!" EXIT; mill route rm todo:TODO'
```

Stop mill connect when the collab ends.
