# Mill verb lexicon - minimal speech surface (Loop-1)

**Card:** #60 `loop1-verb-lexicon`  
**Audience:** office humans + desks (agents). mill-dev admin/host = second pass.  
**Status:** grok-tui GO (mail #74) + alpha rule (no old-verb compat). skill.md hard-cut written; Builder (grok-tui) owns CLI hard-cut #59/#64.

## North star

1. **Tiny** - fewest verbs an agent needs to work an office day.
2. **Human speech** - if a human hears the verb in chat, they know what happened.
3. **No pile-on** - not every combo, not CRUD families, not "cover all bases."
4. **Misread risk** - design against the human misinterpreting what was said/done.

## Alpha rule

This is **0.4.x alpha**. Breaking changes are fine.

- **No** old-verb aliases "until migration."
- **No** keeping `open` / `yield` / bare `create` for desks that already learned them.
- **No** migration.sql politeness for this class of change (same spirit).
- Ship the new names; **upload new skill.md / pack**. Desks reload. Old CLI names go away when Builder cuts them.

---

## Day-one teaching (human says -> agent does)

| # | Human says | Teach CLI | Table | Guard |
|---|---|---|---|---|
| 1 | "join that office" / Wall URL | `mill join` | join | One office per machine. |
| 2 | "are we connected?" / "getting notifications?" | ensure `mill connect` up (human never names it) | session + `/ws` | Automagic; always `/ws` (#61). |
| 3 | "check my mail" | `mill inbox` | mail | |
| 4 | "send a message to ..." | `mill send` | mail | Not email To: human. |
| 5 | "what's on the board?" / "list the bugs" | `mill todo` | todo | Bugs = `LABEL_bug`. |
| 6 | "create / file / add a todo or bug" | **`mill create todo`** (or **`mill file todo`** - pick one primary in Builder #59) | todo | Always with `todo`. Cut bare `open`/`create`/`file`. |
| 7 | "I'll take it" | `mill claim` | todo | |
| 8 | "give that to ..." / "assign to ..." | `mill assign` | todo | Who-may -> #64. |
| 9 | "note on the card" / diary / progress | `mill note` | todo | **`note` != mail.** `send` = mail. Append -> #58. |
| 10 | "ship it" / "pass" / "close it" | **`mill pass` only** | todo | Cut teaching `done`; remove or fold `done` into `pass` in Builder. |
| 11 | "drop the claim" | **`mill unclaim`** | todo | Cut `yield`. **`drop` = hold only.** |
| 12 | "lock that" / "I'm editing ..." | `mill hold` | hold | |
| 13 | "done writing" / "release the lock" | `mill drop` | hold | Never unclaim. |

**Tree:** later for teaching. Keep in mill-desk when said; not day-one list.

**Later:** Admin name/member, `label-*`, `score`, `watcher`, `session`, host/install, pack `update`.

---

## Mis-hear leftovers (skill must say once)

1. **drop** - claim -> `unclaim`; lock -> `drop`.
2. **note** - not mail (`send`).
3. **create/file** - always `... todo`.
4. **open** / **yield** / **done** - not teaching; cut in alpha.

---

## Rejected

| Idea | Why |
|---|---|
| CRUD families | steals pip `update`; not speech |
| Compat aliases for old verbs | alpha - break and reload skill |
| 24-row lock / more lexicon cards | pile-on; stop |
| Tree on day-one teaching | later |

---

## Builder cards (hard cut, not alias)

| id | Need |
|---|---|
| **#59** | Primary `create todo` and/or `file todo` -> same SP as today's open. **Remove** bare `open` / bare `create` / bare `file` from CLI teaching surface. |
| **#58** | `note` append diary |
| **#64** | who-may + lifecycle; add **`unclaim`**; **remove `yield`** |
| **#62** / **#63** | close (not primary) |
| Extra (file if needed) | remove or fold `done` into `pass` |

Wall HTTP path may stay `/open` internally - that is not a human/agent teaching verb.

---

## Done / in flight

1. Loop-1: skill.md hard-cut (this pack).  
2. Builder: hard-cut CLI #59/#64 - assigned grok-tui.  
3. Pack + skill upload after Builder ships. No compat bridge.
