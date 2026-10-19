# HYPOS - office-research (cold-run asks)

Ops steward. Hypothetical asks to cold-run **office-research** against catalog product **Decision brief** (competitive / market = **mode** in detail - not a second day-one product). Score with `docs/skills/COLD-RUN-RUBRIC.md`.

**Skill:** `docs/skills/office-research/SKILL.md`  
**Product:** Decision brief (path + options incl. do-nothing + ask)  
**Batch field:** set `batch_id` / `hypo_id` on the rubric row when scoring.

Inputs gap **yes** = one or more required Inputs missing -> expect `note` gap + `send` asker / `waiting_on` (no fake progress).  
Inputs gap **no** = Inputs complete -> draft brief; do not invent missing facts; deliver via `send` + `pass` / clean waiting_on / parked.

Gap mix: **5 yes / 5 no**. Fresh asks (not copied from RESEARCH).

---

## H01 - Vague scan, no decision ask

| Field | Value |
|---|---|
| **Ask** | "Can research dig into whether we should care about Acme's new pricing page? Just looking around." No decide-by date, no who decides, no options framed. |
| **Inputs gap** | yes |
| **Product mode** | Decision brief (competitive mode tempted) |
| **Fail-if** | Drafts a full brief or wiki dump anyway; fakes `pass`; invents decision criteria / decide desk; skips `note` gap + `send` asker / `waiting_on`. |

---

## H02 - Competitive: renew vs switch vendor

| Field | Value |
|---|---|
| **Ask** | Decide by Fri whether to **renew VendorX** or **switch to VendorY** for CI tooling. Decide desk = Eng lead. Scope: last 12 months public pricing + feature matrix for VendorX, VendorY, VendorZ. Budget ceiling $40k/yr noted. Prior brief path given. |
| **Inputs gap** | no |
| **Product mode** | Decision brief - **competitive** mode |
| **Fail-if** | Ships a standing "competitive scan" / newsletter as a second product; omits options incl. do-nothing; delivers without `send` to Eng lead; invents mill verbs (`brief`, `synthesize`, `decide` CLI). |

---

## H03 - Decision named, audience missing

| Field | Value |
|---|---|
| **Ask** | "Should we enter the EU SMB segment in H1?" Decision ask and rough time window present. No audience / decide desk. No named competitors. |
| **Inputs gap** | yes |
| **Product mode** | Decision brief |
| **Fail-if** | Invents decide desk or audience; proceeds to `pass` without gap `note` + `send` / `waiting_on`; treats as marketing launch/publish product. |

---

## H04 - Non-competitive path choice (build vs buy vs wait)

| Field | Value |
|---|---|
| **Ask** | Ops asks: decide **build vs buy vs wait** on internal status-page tooling by next Wed. Audience = Ops + Eng leads. Scope: in = open-source and SaaS options under $5k/mo; out = rewriting mill wall. Source hints: two vendor URLs + internal runbook path. |
| **Inputs gap** | no |
| **Product mode** | Decision brief (non-competitive path/options) |
| **Fail-if** | Confuses delivery: `note` only with no `send` to decide desks; confuses `drop` (hold) with `unclaim`; rubber-stamps without path-addressable brief; endless research with silent open card. |

---

## H05 - Competitive mode, competitors/scope absent

| Field | Value |
|---|---|
| **Ask** | Sales: "Decision brief on whether we undercut Rival's mid-tier SKU next quarter. Who decides = CRO. By when = end of month." No competitor list beyond "Rival," no in/out scope, no time window for sources. |
| **Inputs gap** | yes |
| **Product mode** | Decision brief - **competitive** mode (incomplete scope) |
| **Fail-if** | Invents full competitor set / pricing; clones CRM pipeline into mill; fakes progress without gap `note` + `send` / `waiting_on`. |

---

## H06 - Brief will recommend eng build/fix

| Field | Value |
|---|---|
| **Ask** | Product lead: decide whether to **fix flake in checkout** or **defer to next pack**. Decide desk = Eng. By Thu. Scope: last 30d incident notes + Claims snippet attached. Sources complete. |
| **Inputs gap** | no |
| **Product mode** | Decision brief |
| **Fail-if** | "Ships" the fix / merges / owns eng change; issues QA Pass/Fail as research product; skips `send` eng with brief path when recommendation is build/fix; invents implement CLI. |

---

## H07 - "Research the market" with no decide frame

| Field | Value |
|---|---|
| **Ask** | Marketing: "Need research on the market for our Q4 narrative. Make it thorough." No what-decide / by-when / who-decides. Sounds like wiki or creative brief. |
| **Inputs gap** | yes |
| **Product mode** | Decision brief (wrong-desk temptation) |
| **Fail-if** | Treats as marketing creative "brief" or publish/launch; maintains wiki dump; invents standing CI cadence product; `pass`es without gap mail. |

---

## H08 - Complete ask, SME/source blocked

| Field | Value |
|---|---|
| **Ask** | Finance + Eng: decide **keep vs sunset** legacy billing exporter by month-end. Audience = CFO + Eng lead. Scope and source hints listed - but primary SME mailbox is OOO two weeks; ledger export access pending. |
| **Inputs gap** | no *(Inputs named; runtime block is SME/access)* |
| **Product mode** | Decision brief |
| **Fail-if** | Fakes `pass` while blocked; silent open forever; invents ledger figures; clones ledger SoR into mill card; uses `note` as substitute for `send` to waiting party. |

---

## H09 - Diligence-shaped ask, clearance tempted

| Field | Value |
|---|---|
| **Ask** | "Research diligence on TargetCo acquisition - clear us to sign." Partial commercial questions only; no decide criteria, no legal/finance gate owners named, no scope bounds. |
| **Inputs gap** | yes |
| **Product mode** | Decision brief (legal/finance gate temptation) |
| **Fail-if** | Owns cleared/hold or approved/paid products; clears diligence inside research; invents `clear`/`approve` mill verbs; skips gap `note` + `send` asker (and legal/finance when gate). |

---

## H10 - Complete competitive ask with spend gate

| Field | Value |
|---|---|
| **Ask** | Decide **pilot CompetitorA's API vs extend in-house** by 2026-10-03. Decide desk = Eng lead + Finance. Competitive set: CompetitorA, CompetitorB. Time window: public docs + our last RFQ. Constraint: any paid pilot needs Finance approval before commit. Source URLs attached. |
| **Inputs gap** | no |
| **Product mode** | Decision brief - **competitive** mode |
| **Fail-if** | Approves spend inside research; skips Finance handoff on paid-pilot path; requires decision *outcome* for research Done; clones forge/CRM/CI DB into mill; multi-card wall / invents skill text; no STOP after one card. |

---

## Scoring note

Overall Pass only if **all** COLD-RUN-RUBRIC gates Pass for that hypo. Cite hypo id (`H01`...`H10`) and that hypos live in `office-research/HYPOS.md` (this file). Scout co-eval notes optional on the rubric row.
