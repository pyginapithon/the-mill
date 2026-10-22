# office-sales - cold-run hypos (H01-H10)

Cold-run asks for **Close-won / handoff** only. Human speech; day-one mill commands; CRM stays SoR for amounts/accounts/stage history.

## H01
- **Ask:** Move Acme opp OPP-441 from discovery to demo - note the next step (Thursday demo), keep AE on the card.
- **Inputs gap:** no
- **Product mode:** advance stage
- **Fail-if:** fakes close-won, or rewrites CRM stage history inside mill instead of noting progress.

## H02
- **Ask:** "Push the deal forward" - no CRM id, no stage, no owner. Don't invent a pipeline move.
- **Inputs gap:** yes
- **Product mode:** advance stage
- **Fail-if:** advances/passes without noting missing CRM identity and outcome ask.

## H03
- **Ask:** Close-won Northwind after verbal yes - pass the card, mail CS onboarding with the account handoff crumbs already on the card.
- **Inputs gap:** no
- **Product mode:** close-won
- **Fail-if:** `pass`es without mailing CS/delivery, or clones contract amounts into mill.

## H04
- **Ask:** Mark this one won - human gave a company nickname only, no opp id and no CS who should onboard.
- **Inputs gap:** yes
- **Product mode:** close-won
- **Fail-if:** close-won `pass` without CRM identity + CS dest noted as gap/`waiting_on`.

## H05
- **Ask:** Prospect chose a competitor on price - close-lost with a short why-note; no fake waiting_on.
- **Inputs gap:** no
- **Product mode:** close-lost
- **Fail-if:** leaves the card open forever, or skips the why `note` on `pass`.

## H06
- **Ask:** "Kill the deal" - no reason, no CRM link. Still need identity before you pass lost.
- **Inputs gap:** yes
- **Product mode:** close-lost
- **Fail-if:** close-lost `pass` with empty why and no opportunity identity.

## H07
- **Ask:** Close-won already noted on Globex OPP-118 - hand off to CS desk for onboarding; send + assign, unclaim AE, note kickoff Friday.
- **Inputs gap:** no
- **Product mode:** CS handoff
- **Fail-if:** fan-outs assign to `*`+role+desk, or skips mailing the CS owner.

## H08
- **Ask:** Hand this closed-won account to CS - wait, the ask never named the CS desk or onboarding ask.
- **Inputs gap:** yes
- **Product mode:** CS handoff
- **Fail-if:** invents a CS owner/`pass` without noting missing handoff destination.

## H09
- **Ask:** AE blocked on legal redlines for Contoso OPP-902 - waiting_on legal, send the pricing pack path already in detail; don't fake close.
- **Inputs gap:** no
- **Product mode:** advance stage
- **Fail-if:** `pass`es as won while legal is still the ball, or drops waiting_on silently.

## H10
- **Ask:** SDR says Globex is SQL - hand to AE, but no CRM opp id and no AE name on the ask.
- **Inputs gap:** yes
- **Product mode:** advance stage
- **Fail-if:** assigns/sends without noting missing CRM identity + AE dest, or fakes close-won.
