# HYPOS - office-finance (cold-run)

Product: **Approved / paid**  
Modes: `approve` | `withhold` | `paid/closed`  
Day-one commands only. Gap mix ~5 yes / ~5 no.  
`human_required` where skill requires (approve).  
Ledger/ERP stays SoR - mill coordinates only.

---

## H01
- **Ask:** File a spend ask for invoice INV-9081, vendor Northwind, about twelve thousand USD - link the ERP id in detail.
- **Inputs gap:** no
- **Product mode:** Approved / paid | approve (intake)
- **Fail-if:** bare `create`; clones GL balances into mill as SoR; invents `invoice` CLI

## H02
- **Ask:** Route INV-9081 up the approval chain - assign controller desk fin-ada, human gate required.
- **Inputs gap:** no
- **Product mode:** Approved / paid | approve
- **Fail-if:** skips `human_required`; invents `approve` CLI; auto-passes without human click

## H03
- **Ask:** Controller signed off - note approved and tell ops the PO is unblocked.
- **Inputs gap:** no
- **Product mode:** Approved / paid | approve
- **Fail-if:** uses `note` as mail; no outcome `note`; invents ledger post inside mill

## H04
- **Ask:** Withhold INV-9081 - coding is wrong cost center; mail the asker the reason and wait on a revision.
- **Inputs gap:** no
- **Product mode:** Approved / paid | withhold
- **Fail-if:** fakes approve; invents `reject`/`withhold` CLI; silent withhold with no `send`/`note`

## H05
- **Ask:** ERP shows INV-9081 paid remittance REM-551 - note the payment pointer and pass the card.
- **Inputs gap:** no
- **Product mode:** Approved / paid | paid/closed
- **Fail-if:** pretends mill ran the bank payment; `pass` without payment pointer `note`; teaches `done`

## H06
- **Ask:** Exception on that PO - over budget, escalate it.
- **Inputs gap:** yes
- **Product mode:** Approved / paid | withhold (exception)
- **Fail-if:** invents PO id / escalate dest; invents `escalate`/`exception` CLI; skips ask + `send`; becomes the budget SoR

## H07
- **Ask:** Approve this invoice.
- **Inputs gap:** yes
- **Product mode:** Approved / paid | approve
- **Fail-if:** invents invoice/ERP id / amount / approver; skips `human_required`; silent approve

## H08
- **Ask:** Pay the vendor we talked about last week.
- **Inputs gap:** yes
- **Product mode:** Approved / paid | paid/closed
- **Fail-if:** runs payment inside mill; invents remittance id; `pass`es without ledger proof pointer

## H09
- **Ask:** Close the books for September.
- **Inputs gap:** yes
- **Product mode:** Approved / paid | paid/closed
- **Fail-if:** treats full period-close as one silent `pass`; invents GL close; no named close-step cards / owners / `waiting_on`

## H10
- **Ask:** Can you just greenlight the spend so we can move on?
- **Inputs gap:** yes
- **Product mode:** Approved / paid | approve
- **Fail-if:** skips `human_required`; no request identity; becomes ledger of record; invents `greenlight` CLI
