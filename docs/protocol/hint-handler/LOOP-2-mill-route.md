# Loop-2 - mill route CLI + package hint-handler

**Date:** 2026-09-20 PT  
**Steward note** (no mill todo filed - `mill` on this box cannot reach mill-wall / file a real dest card; note-only is enough).

## Need

Tracking: Loop-2 **#387** `mill-route-cli-ship` (label `bug`), noted on **#386**.

1. **Shipped.** `mill route add|rm|list` is the arm (card 387, route.md). Cold desks follow `SKILL.md`: write the handler, arm with `--owner` before the key, then `mill add TYPE:ID --hint`. Vendor poke is only the no-route fallback.
2. **Builder packages** this draft into the-mill at `docs/protocol/hint-handler/` (SKILL, TEMPLATE, examples, tools) so mill-desk can point at a living SoR and agents stop using `/workspace/mill-docs/hint-handler/`.

## Out of scope here

- Inventing a mill todo id without a real `mill create todo` dest.
- Patching installed mill package or mill-desk skill from this steward draft.

## Done when

- `mill route add|list|rm` works on the mill connect PC per route.md.
- Package ships `docs/protocol/hint-handler/`; mill-desk DO line can be applied from `MILL-DESK-DO-LINE.md`.
