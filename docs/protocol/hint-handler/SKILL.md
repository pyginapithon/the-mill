---
name: hint-handler
description: >
  Cold-desk playbook: customize one watcher HINT, write a deterministic handler,
  arm it with mill route. Use after the human approves background mode.
  Not a second mill CLI. Cite connect/route/hints.
metadata:
  short-description: "HINT handler: program, mill route, watcher recipe, drop"
---

# HINT handler - background program map

**Cold desk:** read [COLD.md](COLD.md) and `examples/stub_handler.py` only. Do not open the rest of this file, or philosophy, hints, route, connect, or JOIN, unless a command there exits non-zero.

**When:** human asks a task -> collab needed -> agent explains modes (incl. background HINT handler) -> **human approves background**. Then this skill.

**Cite when a step failed:** `docs/protocol/philosophy.md`, `connect.md`, `route.md`, `hints.md`, `JOIN.md`. Chat inbound stays mill-desk / skill.md.

**Not this skill:** chat inbound (mill-desk). Default vendor poke when no route hits (route.md). Inventing mill verbs.

## Lifecycle (program -> route -> watcher -> trigger -> drop)

### Guards

No poll. No invented mill verbs. Exit **0**. `heartbeat:PING` and `join:JOIN` are dropped on receive, before any route program. Do not arm `join:JOIN`. A missing route does not vendor-poke JOIN.

A watcher is **one desk on one of** `todo`, `join`, `hold`, `score`, or a name id (`name`). Mail is not a watcher type. Mail arrives as a push. Trees, labels, and memberships organize work. They are not watch targets. `roster_id` is only the project or role collection. Another desk attaches its own watcher. Do not expect every project member to be watched.

Vendor poke, when no route hits, is the fallback. It is not this playbook. A future vendor webhook is that same fallback, not a second router.

### 1. Write the handler first

Copy `examples/stub_handler.py` to `~/.mill/handlers/DESK_<desk>/on_mail.py`. Import `tools.hint_handler`. Call `parse_stdin()` with **no argument**. Passing `sys.stdin` raises `TypeError`.

`ev.detail` is this desk's `watcher.hint` string, or the cheap default `{what,id,when,state,watchers,tree}` when that hint is empty. The wire `hint` stays `TYPE`. The route key stays `mail:MAIL`, `todo:TODO`, and so on. A recipe does not change the key.

`log()` writes stderr. mill connect **discards the route child's stdout and stderr**. A print is not evidence. The stub appends one line to `hint-evidence.jsonl` beside the program (`detail_kind` is `recipe` or `default`). Replace that write with the mill verb the task needs. `hint drain ok=1` means the program **started**, not that it exited 0.

Keep the program. Reuse it. It is not package code.

### 2. Arm

`--owner` goes **before** the key. Everything after the key is the program. A flag after the key becomes part of the program argv, and the route is saved for the sticky desk instead. This is the only place that rule is spelled out.

```text
mill route add --owner <desk> mail:MAIL -- python ~/.mill/handlers/DESK_<desk>/on_mail.py
mill route add --owner <desk> todo:TODO -- python path/to/on_todo.py
mill route add --owner <desk> * -- python path/to/desk_handler.py
```

The list is a chain in add order; `*` sits where it was added. Exit 0 = handled (stop). Print `not-mine` last and exit 0 to pass to the next redirector. mill connect re-reads the chain on every frame. No restart.

Then bring connect up. One dest, one mill connect:

```text
mill connect --owner <desk> --vendor <vendor> [--session <uuid>]
```

### 3. Customize the HINT, then trigger

After connect is up, attach this desk to **that activity**:

```text
mill add todo:<id> --hint "need,status"
```

Empty hint restores the cheap default. The recipe is a short field list for **your** program. mill does not parse it.

The trigger is a **later write** on that same activity (claim, hold refresh, score the same name, or `mill label-add` on that id). A write from before connect is up is a missed push. It is not replayed.

`mill send` pushes MAIL to each dest. It does not use `watcher`. `mill create todo` pokes inside the insert. That first poke is before a custom `--hint` can exist on the new id. Read the id from the insert JSON, set `mill add`, then a second write on that same id. `mill label-add <type> <id> bug` is that second write when the label `bug` already exists.

### 4. Run (on each HINT)

stdin is one JSON object `{type,id,hint,detail?}`.

1. `parse_stdin()` -> if `ev.ignore`, exit 0.
2. Read `ev.detail`. mill-fetch leftovers only when the recipe still needs the book (MAIL inbox, that one TODO - no full board).
3. Task mill-verbs only. **STOP**.
4. Exit **0**. mill connect does not mill-update for exit 0.

### 5. Drop

```text
mill route rm --owner <desk> mail:MAIL
```

Stop mill connect when the collab ends. Switching foreground and background: stop the old connect, then start the new mode.

## Worked paths (short)

| Path | Arm | Customize | On HINT |
| :--- | :--- | :--- | :--- |
| MAIL | `mill route add --owner <desk> mail:MAIL -- python .../on_mail.py` | no watcher. The send push is the trigger | parse -> detail -> inbox leftovers only if needed -> STOP -> exit 0 |
| TODO | `mill route add --owner <desk> todo:TODO -- python .../on_todo.py` | `mill add todo:<id> --hint "need,status"` | parse -> detail -> that card only -> STOP -> exit 0 |

See `HINT-HANDLER.TEMPLATE.md`, `examples/stub_handler.py`, `tools/hint_handler/`.

## Awareness DO (mill-desk - proposed, not applied here)

> **DO:** When collab needs background HINTs, load **hint-handler** after human approves background - see connect.md + this skill.

Patch suggestion: `MILL-DESK-DO-LINE.md` in this folder. Do not edit installed mill-desk until package SoR lands.
