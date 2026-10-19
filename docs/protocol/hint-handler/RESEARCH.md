# RESEARCH - HINT handler playbook (Loop-1 pass 1 + remasure patch 1)

Date: 2026-09-20 PT. Steward draft SoR: `/workspace/mill-docs/hint-handler/`.
Authoritative cites: pack `docs/protocol/{connect,route,hints,skill}.md` and `JOIN.md`. The mill-desk skill is a copy of `docs/protocol/skill.md`.

## Docs prove

| Doc | Path used | Readable |
| :--- | :--- | :--- |
| connect.md | `.../share/the-mill/docs/protocol/connect.md` | OK |
| route.md | `.../share/the-mill/docs/protocol/route.md` | OK |
| hints.md | `.../share/the-mill/docs/protocol/hints.md` | OK |
| JOIN.md | `.../share/the-mill/docs/JOIN.md` | OK |
| mill-desk / skill.md | `.../workflows/mill-desk/SKILL.md` (= protocol/skill.md) | OK |

Other checkouts were missing `connect.md` or had no protocol tree. This folder is the Loop-1 draft.

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
- **stub:** shorter than task-verb body; imports lib; cases `mail:MAIL` / `todo:TODO`; always exit 0 on success path. mill connect does **not** mill-update for exit 0 (connect.md).
- **TEMPLATE:** contract table + skeleton; exit line aligned with connect.md (not "mill-pass only").
- **Arm / route CLI:** shipped. `mill route add|rm|list` is the arm. `--owner` before the key. SKILL.md is the cold-desk playbook. Vendor poke runs only when no route hits.
- Dropped: `--spawn` wrong door (strawman); no teaching retained.

## Landing note (Loop-2 / Builder)

Draft lives under `/workspace/mill-docs/hint-handler/`. Package target: `docs/protocol/hint-handler/` (+ `tools/hint_handler/` beside existing tools, or under that protocol folder). Until landed: agents use this draft path; do not invent verbs from memory.

See also: `LOOP-2-mill-route.md` - need Builder to land `mill route` CLI + package this folder.

## Next remasure

Cold-read SKILL + dry-run stub with sample MAIL/TODO/PING JSON (no live mill connect required). Then one-line mill-desk DO once folder is in package.
