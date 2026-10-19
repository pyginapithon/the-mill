# REMEASURE-PATCH-1 - Gardener Fail remasure fixes

**Date:** 2026-09-20 PT  
**SoR:** `/workspace/mill-docs/hint-handler/`  
**Cites:** connect.md, route.md, hints.md (installed package).  
**Not touched:** installed mill package, mill-desk skill.

## File-by-file

| File | Change |
| :--- | :--- |
| `tools/hint_handler/__pycache__/` | **Deleted** entirely (and any `.pyc`). Re-cleared after stub dry-run (import regenerates bytecode). |
| `SKILL.md` | Merged long `## Must-not` into thin **Guards** (3 lines) under Lifecycle. Elevated Arm: **`mill route` CLI not shipped** -> **Arm blocked in product**; today teach connect.md stub/vendor-poke; `mill route add` = documented shape only. Replaced bare `mill connect up` with outcome prose + `mill connect --owner <desk> --vendor ...`. Exit line keeps connect.md: mill connect does **not** mill-update for exit 0. |
| `HINT-HANDLER.TEMPLATE.md` | Exit line: prefer "mill connect does **not** mill-update for exit 0"; dropped "no mill-pass for exit 0" phrasing. Arm section: stub/vendor poke today; route add = documented shape only. Kept import-lib; sys.path note "until packaged". |
| `examples/stub_handler.py` | Arm comments aligned (stub/vendor poke today; route = shape only). Exit comment = mill-update phrasing. sys.path: "until packaged". Import-lib kept (Pass). |
| `tools/hint_handler/lib.py` | `leftovers()` TODO path: **do not** dump full `mill todo` board; if detail insufficient, return `""` and let task narrow to `ev.id`. Prefer detail when recipe fields present. MAIL still inbox (unread). |
| `MILL-DESK-DO-LINE.md` | Deleted dead ``(`mill briefing connect`)`` from current + proposed base lines. |
| `RESEARCH.md` | Aligned with SKILL: Arm blocked / route not shipped / stub/vendor-poke today; leftovers no full board; exit = mill-update phrasing. |
| `LOOP-2-mill-route.md` | **Created** - Builder need: land `mill route` CLI + package `docs/protocol/hint-handler/`. No mill todo filed (mill-wall unreachable / no real dest). |
| `REMEASURE-PATCH-1.md` | This log. |

## Stub dry-run (post-patch)

| HINT | exit |
| :--- | ---: |
| MAIL `{"type":"mail","id":42,"hint":"MAIL",...}` | 0 |
| TODO `{"type":"todo","id":14,"hint":"TODO",...}` | 0 |
| PING `{"type":"heartbeat","id":0,"hint":"PING"}` | 0 |
| JOIN `{"type":"join","id":1,"hint":"JOIN"}` | 0 |

TODO leftovers logged "no full board; task narrows to that card" (no board dump).

## Residual gaps (for Gardener re-remasure)

- Product Arm still blocked until Builder ships `mill route` (Loop-2 note).
- mill-desk DO line still proposed-only (do not garden installed skill).
- Package landing path still draft under `/workspace/mill-docs/hint-handler/`.

## Residual cleanup note

Removed the obsolete wrong-door flag/path teaching from `SKILL.md`, `HINT-HANDLER.TEMPLATE.md`, and `examples/stub_handler.py`; each now teaches only the connect.md stub/vendor poke.
