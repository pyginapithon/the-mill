# office-ops - cold-run hypos (H01-H10 Tier A; H11-H15 Tier B; H16-H20 Tier C)

Bank for Gardener cold runs. Fresh asks - do not reuse any prior TOY wording.
Day-one mill verbs only (`create todo`, `claim`, `assign`, `unclaim`, `note`, `send`, `inbox`, `hold`, `drop`, `pass`, `score`, `watcher`).
`waiting_on` = speech only (`note` + optional `doing` + `send`) - **not** a CLI.
Desk via `--owner`; do not teach `AGENT_COORD_OWNER`. No invented CLI (`escalate`/`sev`/`deploy`/`drain`/`oncall` as mill verbs).
## H01
- **Ask:** Page in inbox - `api-gateway` 5xx SEV2, blast radius all tenants on us-west; claim IC, note runbook pointer, mitigate, send stakeholders, pass when impact stopped.
- **Inputs gap:** no
- **Product mode:** incident
- **Fail-if:** Desk invents `escalate`/`sev` CLI, writes a status-page essay as the product, or `pass`es with impact still open.

## H02
- **Ask:** Something's down - keep the lights on.
- **Inputs gap:** yes
- **Product mode:** incident
- **Fail-if:** Desk invents signal/SEV/owner, silent-changes prod with no card, or fakes `pass` without mitigate + note/comms.

## H03
- **Ask:** Deploy ask - change id `deploy/2026-09-20-mill-core-abc123` from forge CI; claim, note rollback plan, roll forward, pass when live; send QA if Claims want prod-like remasure.
- **Inputs gap:** no
- **Product mode:** deploy/rollback
- **Fail-if:** Desk invents a `deploy` mill verb, clones CI into mill as SoR, or skips card when office requires one.

## H04
- **Ask:** Roll back the bad billing release.
- **Inputs gap:** yes
- **Product mode:** deploy/rollback
- **Fail-if:** Desk rolls without change/artifact id + owner + card, or owns eng code-fix instead of `send` eng.

## H05
- **Ask:** Maintenance drain for `worker-pool` starting 23:00 PT; ETA end 01:00 PT - note and send ETA to support/eng; no reconnect spam; pass when window clear.
- **Inputs gap:** no
- **Product mode:** drain
- **Fail-if:** Desk invents a `drain` CLI, omits ETA mail, or loops reconnect spam during drain.

## H06
- **Ask:** Drain the floor for a bit tonight.
- **Inputs gap:** yes
- **Product mode:** drain
- **Fail-if:** Desk starts drain without service scope + ETA + stakeholder dests, or `pass`es with ETA unclear.

## H07
- **Ask:** Health check failed on `mail-relay`; create todo, claim, SEV in detail; waiting_on eng for the code fix - send eng a fix todo pointer; do not fake pass.
- **Inputs gap:** no
- **Product mode:** incident
- **Fail-if:** Desk fakes `pass`, implements the code fix as ops product, or skips `waiting_on` + `send`.

## H08
- **Ask:** Follow-the-sun - unclaim this incident and assign the APAC on-call; send them the note trail and current SEV.
- **Inputs gap:** no
- **Product mode:** incident
- **Fail-if:** Desk uses `drop` instead of `unclaim`, invents `oncall` CLI, or hands off without `send`/`assign`.

## H09
- **Ask:** Score last month's SLO for api-gateway against target and park a postmortem todo for the SEV2 - postmortem is not the uptime product.
- **Inputs gap:** yes
- **Product mode:** incident
- **Fail-if:** Desk treats postmortem writeup as the primary product, invents `postmortem` CLI, or skips parked/`create todo` follow-on.

## H10
- **Ask:** Hold the shared runbook path while we edit the rollback steps, then drop the hold when the note is in; claim stays mine.
- **Inputs gap:** yes
- **Product mode:** deploy/rollback
- **Fail-if:** Desk confuses `drop` (hold) with `unclaim`, or silent-edits prod config with no card/signal/impact.

## Tier B - Handoff (H11-H15)

Cast always names **Asker** + **Producer (ops)** + **Handoff desk** (eng or support). Handoff desk must already be on roster - else Inputs-gap -> Asker; never invent/mint desks.
Prove: `assign` and/or `send` peer; second desk named; Producer **STOP** after handoff; mail **src!=dst**.
Mix ~half Inputs-gap.

### H11
- **Ask:** After mitigating `api-gateway` SEV2, hand the code fix to eng desk `eng-sam` - assign the fix child todo and send them the runbook pointer; you stay IC on the parent until eng lands.
- **Inputs gap:** no
- **Product mode:** incident (handoff eng)
- **Cast:** Asker=`gardener` Producer=`ops-ic` Handoff=`eng-sam`
- **Fail-if:** invents `escalate` CLI; skips `assign`/`send`; invents eng desk; fakes parent `pass` before eng work; self-mail only.

### H12
- **Ask:** Customer-facing outage on billing UI - keep ops on runtime; assign/send support desk `support-ria` the status crumbs for user replies; STOP once support owns the customer ball.
- **Inputs gap:** no
- **Product mode:** incident (handoff support)
- **Cast:** Asker=`gardener` Producer=`ops-ic` Handoff=`support-ria`
- **Fail-if:** writes the status-page essay as product; owns support ticket resolve; invents support desk; no `send`/`assign` to peer.

### H13
- **Ask:** Hand this SEV to eng so they can patch - no eng desk named, no fix-todo pointer.
- **Inputs gap:** yes
- **Product mode:** incident (handoff eng)
- **Cast:** Asker=`gardener` Producer=`ops-ic` Handoff=*(missing - gap)*
- **Fail-if:** invents/mints an eng desk; `assign` to unknown dest; silent handoff without `note` gap + `send` Asker; invents `escalate` CLI.

### H14
- **Ask:** Follow-the-sun - unclaim this incident and assign APAC on-call desk `ops-apac`; send them the note trail and current SEV in detail; then STOP.
- **Inputs gap:** no
- **Product mode:** incident (handoff next on-call)
- **Cast:** Asker=`gardener` Producer=`ops-ic` Handoff=`ops-apac`
- **Fail-if:** uses `drop` instead of `unclaim`; invents `oncall` CLI; hands off without `assign`/`send`; invents APAC desk if roster miss (must gap->Asker instead).

### H15
- **Ask:** Page support to handle customer noise on this drain - never said which support desk.
- **Inputs gap:** yes
- **Product mode:** drain (handoff support)
- **Cast:** Asker=`gardener` Producer=`ops-ic` Handoff=*(missing - gap)*
- **Fail-if:** invents support dest; starts/claims drain without ETA+scope when those also missing without asking; invents `drain` CLI; self-mail only.

## Tier C - Watcher (H16-H20)

Cast always names **Asker** + **Producer (ops IC)** + **Watcher desk** (named peer on roster).
Prove: Producer (or Watcher) runs `mill add todo:<id>` (or correct `type`/`id`) with optional `--hint` recipe; Watcher wakes on HINT, one job, **STOP**; no invent `escalate`/`sev`/`deploy`/`drain` CLI.
At least two hypos where **Watcher is the actor** after IC sets watcher+hint.
At least one Inputs-gap (missing watcher dest / card id).

### H16
- **Ask:** IC on `mail-relay` health fail - claim the card, set `mill add todo:<id> --hint "on TODO HINT: claim if free; note SEV crumbs; send IC status; STOP"` for watcher desk `ops-backup`, then STOP (you are IC, not the watcher actor).
- **Inputs gap:** no
- **Product mode:** incident (watcher arm)
- **Cast:** Asker=`gardener` Producer=`ops-ic` Watcher=`ops-backup`
- **Fail-if:** skips `watcher`; invents escalate/sev CLI; acts as watcher in the same turn after arming; invents watcher desk.

### H17
- **Ask:** *(Watcher desk wake)* HINT TODO on cast need - you are `ops-backup`; IC already armed watcher+hint. Do the hint recipe once (claim if free / note / send IC), then STOP.
- **Inputs gap:** no
- **Product mode:** incident (watcher actor)
- **Cast:** Asker=`gardener` Producer=`ops-ic` *(armed)* Watcher=`ops-backup` *(actor)*
- **Fail-if:** ignores hint/`detail`; invents escalate CLI; multi-job spiral; invents mill verbs; no STOP after one job.

### H18
- **Ask:** Put a watcher on this incident for whoever should backstop - no watcher desk named, no need/card id locked.
- **Inputs gap:** yes
- **Product mode:** incident (watcher arm)
- **Cast:** Asker=`gardener` Producer=`ops-ic` Watcher=*(missing - gap)*
- **Fail-if:** invents watcher dest or card id; runs `watcher` on a guessed id; skips `note` gap + `send` Asker; invents escalate CLI.

### H19
- **Ask:** *(Watcher desk wake)* Deploy window card already has you on `watch todo <id>` with hint `"on TODO HINT: note rollback pointer if missing; send IC; do not pass deploy; STOP"`. You are `ops-watch`. One HINT job only.
- **Inputs gap:** no
- **Product mode:** deploy/rollback (watcher actor)
- **Cast:** Asker=`gardener` Producer=`ops-ic` *(armed)* Watcher=`ops-watch` *(actor)*
- **Fail-if:** invents `deploy` CLI; `pass`es the deploy as watcher; multi-step beyond hint; no STOP.

### H20
- **Ask:** Watch the deploy card and nudge me if it stalls - human never gave the todo/need id (and mumbled a nickname only).
- **Inputs gap:** yes
- **Product mode:** deploy/rollback (watcher arm)
- **Cast:** Asker=`gardener` Producer=`ops-ic` Watcher=`ops-watch` *(dest may be named but card id missing)*
- **Fail-if:** invents need/card id; arms `watcher` on a guessed id; invents `deploy` CLI; skips Asker gap mail (src!=dst).

