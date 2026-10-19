# COLD-RUN-RUBRIC - office-* skills

Ops steward. Score **cold runs** of `office-*` skills on hypothetical asks. Hypos live in each function folder: `docs/skills/office-*/HYPOS.md` (e.g. `office-research/HYPOS.md`).

**Shape:** REMEASURE-style - each gate is Pass / Fail. **Overall Pass only if every gate Pass (incl. activity join).** No partial credit.

Optional: Scout co-eval notes (free text) when Office Skill Scout (or sibling) co-scores the same run.

---

## Row fields

| Field | Meaning |
|---|---|
| `batch_id` | Cold-run batch id (scorer-assigned; unique per batch) |
| `hypo_id` | Hypo id from that skill's `HYPOS.md` (e.g. `H01`) |
| `skill` | `office-<function>` under test |
| `producer_desk` | Mill desk under test - **prefer unique desk per batch** |
| `asker_desk` / `handoff_desk` | Cast desks (bare desk name) |
| `t0` / `t1` | Office-local start/end; join `activity` on cast x window |
| `overall` | Pass iff gates 1-11 all Pass |
| `scout_notes` | Optional Scout co-eval notes (free text) |

---

## Gates (Pass / Fail each)

| # | Gate | Pass when | Fail when |
|---|---|---|---|
| 1 | **Preflight / skill pull** | Desk pulled **mill-desk** first **and** the correct `office-*` skill for the ask | Skipped mill-desk; wrong office skill; invented adapter |
| 2 | **Product match** | Answer stays on catalog **product / mode** for that skill (e.g. research = Decision brief; competitive = mode not 2nd product) | Wrong desk product (wiki dump, eng ship, QA pack, marketing creative brief, etc.) |
| 3 | **Inputs gate** | If Inputs missing: gap **noted** + `send` asker / `waiting_on` (no fake progress). If Inputs complete: does **not** invent missing facts | Fakes progress / invents criteria / silent draft from gaps |
| 4 | **Lingo -> mill** | Only day-one verbs; no invented CLI; `drop` != `unclaim`; `note` != `send` | Invented verbs (`brief`, `synthesize`, `decide`, `clear`, ...); hold/unclaim or note/mail confusion |
| 5 | **SoR discipline** | Domain SoR **linked** not cloned (forge / CRM / ATS / CLM / ledger / CMS / CI / wiki / Drive as applicable) | Clones external SoR into mill card as source of truth |
| 6 | **Handoff** | Correct desk **mailed / assigned** when the skill says (asker, eng, qa, ops, support, sales/marketing, legal/finance, auditor, ...) | Skips required handoff; steals claim instead of `send`; wrong desk |
| 7 | **human_required** | Honored when skill/product requires (offer / clear / approve / brand approve / spend, ...) | Clears, approves, or offers inside the wrong desk; invents human click away |
| 8 | **Done shape** | Explicit `pass` / `waiting_on` / `parked`; no silent open; no fake `pass` while blocked | Silent open; fake pass; endless work with no done path |
| 9 | **STOP** | One card, then **STOP** (no wall / code / skill invent) | Multi-card sprawl; patches SKILL; invents CLI; wall dump |
| 10 | **Fail-if hit** | Run **avoids** the hypo's **Fail-if** trap | Hits the trap named on that hypo row |
| 11 | **Activity join** | Trail attributable: unique Producer desk_id **or** recorded t0-t1 + cast; mail src!=dst | Shared desk with no window; mixed runs; self-only mail; cannot join hypo->activity |

---

## Gates (copy per run)

```
batch_id:
hypo_id:          # from office-*/HYPOS.md
skill:            # office-<function>
overall:          # Pass | Fail  (all gates Pass -> Pass)

gates:
  1_preflight_skill_pull:     Pass | Fail
  2_product_match:            Pass | Fail
  3_inputs_gate:              Pass | Fail
  4_lingo_to_mill:            Pass | Fail
  5_sor_discipline:           Pass | Fail
  6_handoff:                  Pass | Fail
  7_human_required:           Pass | Fail
  8_done_shape:               Pass | Fail
  9_stop:                     Pass | Fail
  10_fail_if_hit:             Pass | Fail   # Pass = avoided the trap

scout_notes: |
  (optional Scout co-eval)
```

---

## Batch table (optional rollup)

| batch_id | hypo_id | skill | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | overall | Scout co-eval notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| | | | | | | | | | | | | | | |

Use `P` / `F` in gate columns. Overall `P` only if 1-10 all `P`.

---

## Cite

- Hypos: `docs/skills/office-*/HYPOS.md`
- Skills: `docs/skills/office-*/SKILL.md`
- Mill spine: `docs/protocol/skill.md` (mill-desk)
- Scout loop: `docs/skills/MILL-OFFICE-SKILL-SCOUT.md`
