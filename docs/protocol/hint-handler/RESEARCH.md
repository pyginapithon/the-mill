# RESEARCH - HINT handler playbook (Loop-1 pass 1 + remasure patch 1)

Date: 2026-09-20 PT. Playbook: `docs/protocol/hint-handler/`.
Authoritative cites: pack `docs/protocol/{connect,route,hints,skill}.md` and `JOIN.md`. The mill-desk skill is a copy of `docs/protocol/skill.md`.

## Docs prove

| Doc | Path used | Readable |
| :--- | :--- | :--- |
| connect.md | `.../share/the-mill/docs/protocol/connect.md` | OK |
| route.md | `.../share/the-mill/docs/protocol/route.md` | OK |
| hints.md | `.../share/the-mill/docs/protocol/hints.md` | OK |
| JOIN.md | `.../share/the-mill/docs/JOIN.md` | OK |
| mill-desk / skill.md | `.../workflows/mill-desk/SKILL.md` (= protocol/skill.md) | OK |

Other checkouts were missing `connect.md` or had no protocol tree. This measure is the Loop-1 pass.

## Measure A-H (before this patch)

| | Present? | Path / note | Gap |
| :--- | :--- | :--- | :--- |
| A Awareness | partial | connect/JOIN/mill-desk explain fg vs bg -> route | No named hint-handler DO line |
| B Skill | absent | - | No `docs/protocol/hint-handler/SKILL.md` |
| C Specs | scattered | connect/route/hints | No consolidated handler contract playbook |
| D Examples | partial | sanitize `route-template.py`; route.md MAIL/TODO table | No hint-handler MAIL+TODO worked path |
| E Templates | absent | - | No `HINT-HANDLER.TEMPLATE.md` (route-template != named playbook) |
| F Lib | absent | - | No `tools/hint_handler/` |
| G Cross-links | partial | connect<->route<->hints | No pointer to hint-handler skill |
| H RESEARCH | absent | - | This file |

Search: no `hint-handler` / `HINT-HANDLER` / `tools/hint_handler` hits in mill trees before this draft.

## Kept / dropped

| Candidate | Verdict | Why |
| :--- | :--- | :--- |
| Full playbook essay in mill-desk | DROP | Prefer pointer; mill-desk stays chat map |
| Duplicate route.md / hints.md | DROP | Cite, don't rewrite |
| Reuse sanitize `route-template.py` only | DROP as sole ship | Exists but unnamed playbook; installed package lacks template file |
| Thin lib + stub + TEMPLATE + SKILL | **KEEP** | Smallest stub/vendor-poke->run->drop slice |
| Patch installed mill-desk now | DROP | Not living package SoR; propose DO line only |
| Second mill CLI in lib | DROP | Wrappers call `mill` / `agent_coord` only |
| Polling helpers | DROP | Guards per connect.md |
| Full `mill todo` board in leftovers | DROP | route.md/hints.md = that card; return "" and let task narrow |

## Stub / lib shape (why)

- **lib:** parse stdin JSON -> `HintEvent` (`route_key`, `detail` parse, ignore PING/JOIN); `leftovers()` = MAIL inbox / TODO that-card-or-"" (never full board); `run_mill` thin; exit helpers. Matches route.md "Is the HINT enough?" table + hints.md agent order.
- **stub:** shorter than task-command body; imports lib; cases `mail:MAIL` / `todo:TODO`; always exit 0 on success path. mill connect does **not** mill-update for exit 0 (connect.md).
- **TEMPLATE:** contract table + skeleton; exit line aligned with connect.md (not "mill-pass only").
- **Arm / route CLI:** shipped. `mill route add|rm|list` is the arm. The desk is the sitting connect; commands run in that parent shell. SKILL.md is the cold-desk playbook. Vendor poke runs only when no route hits.
- Dropped: `--spawn` wrong door (strawman); no teaching retained.

## Landing

The playbook is `docs/protocol/hint-handler/`. `mill route add|rm|list` ships. The wheel includes `COLD.md`.

## Next remasure

Cold-read SKILL + dry-run stub with sample MAIL/TODO/PING JSON (no live mill connect required).

## 2026-10-20 - mill todo #353

- Deleted `REMEASURE-PATCH-1.md`, `LOOP-2-mill-route.md`, and `MILL-DESK-DO-LINE.md`. They still said `mill route` was blocked or not packaged. The command ships.
- `--owner` is not on `mill route` or `mill connect`. The desk is the sitting connect. Desk commands run in that same parent shell: `bash -c 'mill connect DESK >/dev/null 2>&1 & trap "kill $!" EXIT; mill COMMAND'`.
- Tag commands are `mill label` and `mill unlabel`.
- A letter frame is `{kind: mail}` (no `type` or `hint`). Its route key is `mail:MAIL`. The lib follows `route_chain.route_key` (PR #31).
- Vendor-poke fallback, in `spawn.md`: `AGENT_COORD_SPAWN`, then `<desk>.spawn` (`type:hint`, then `*`), then config `spawn`, then `bot_wake_cmd`. A letter does not match `mail:MAIL` on that map.
