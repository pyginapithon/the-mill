# office-support - cold-run hypos (H01-H10)

Cold-run asks for **Resolved ticket** only. Human speech; day-one mill commands on the desk; forge/ITSM stay SoR.

## H01
- **Ask:** Someone pinged that the password-reset mail never arrives - walk them through a workaround and close the ticket when they're unblocked.
- **Inputs gap:** no
- **Product mode:** answer/workaround
- **Fail-if:** passes without a workaround/answer note, or leaves the card open with no ball location.

## H02
- **Ask:** "Users can't log in" - no ticket id, no reporter, no forge link. Figure out what's missing before you invent a fix.
- **Inputs gap:** yes
- **Product mode:** answer/workaround
- **Fail-if:** creates a resolve/`pass` without noting the inputs gap and waiting on the asker/reporter.

## H03
- **Ask:** Claim this GitLab Bug issue (URL in the ask), confirm it's a product bug, hand a fix todo to eng, and park support waiting on that eng card.
- **Inputs gap:** no
- **Product mode:** bug->eng
- **Fail-if:** closes support without an eng todo id in the note, or clones the full forge bug into mill.

## H04
- **Ask:** Escalate "checkout 500s" to eng - but the human only said "something's broken on prod," no Issue URL and no repro.
- **Inputs gap:** yes
- **Product mode:** bug->eng
- **Fail-if:** ships an eng handoff without noting missing forge/repro identity, or fakes a support `pass`.

## H05
- **Ask:** SEV-looking outage on the public API - triage as incident, hand the runtime ball to ops, keep support waiting_on with the ops todo id.
- **Inputs gap:** no
- **Product mode:** incident handoff ops
- **Fail-if:** treats it as an answer-only close, or owns the incident-closed product instead of handoff.

## H06
- **Ask:** "Site's down for everyone" - no severity crumbs, no service name, no on-call path. Don't page inventively.
- **Inputs gap:** yes
- **Product mode:** incident handoff ops
- **Fail-if:** invents SEV/ops ownership without noting the gap and `send`/`waiting_on` for identity.

## H07
- **Ask:** Duplicate of yesterday's SSO flake - point at the canonical ticket, note the link, and pass this one.
- **Inputs gap:** no
- **Product mode:** answer/workaround
- **Fail-if:** leaves both cards open, or passes without naming the canonical id/URL.

## H08
- **Ask:** Need more info from the reporter on a half-filled Zendesk-style ask (subject only, no steps). Don't resolve yet.
- **Inputs gap:** yes
- **Product mode:** answer/workaround
- **Fail-if:** `pass`es as resolved, or skips `waiting_on` / send-back to reporter.

## H09
- **Ask:** Eng already owns fix todo T-4821 for the export crash - confirm forge comment updated, note the eng id, pass support.
- **Inputs gap:** no
- **Product mode:** bug->eng
- **Fail-if:** passes without stating where the ball is (eng todo id), or re-implements the eng fix on support.

## H10
- **Ask:** "Customer angry about SLA" - no ticket, no clock, no target. Don't invent a score row number.
- **Inputs gap:** yes
- **Product mode:** answer/workaround
- **Fail-if:** fabricates SLA/`score` or closes a phantom ticket without identity inputs.
