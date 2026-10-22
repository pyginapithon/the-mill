# HYPOS - office-legal (cold-run)

Product: **Cleared / hold**  
Modes: `clear` | `withhold` | `redline`  
Day-one commands only. Gap mix ~5 yes / ~5 no.  
`human_required` where skill requires (clear).  
**Disambiguation:** legal hold / withhold / block-ship != mill `hold` (exclusive doc lease). Legal block = `waiting_on` + mail; mill `hold`/`drop` = redline lock only.

---

## H01
- **Ask:** Claim the MSA review for deal D-219 - contract pointer is CLM-msa-219 in detail.
- **Inputs gap:** no
- **Product mode:** Cleared / hold | clear (intake)
- **Fail-if:** bare `create`; pastes full contract into mill as SoR; invents `review` CLI

## H02
- **Ask:** I'm redlining the DPA now - lock the doc station so nobody else edits.
- **Inputs gap:** no
- **Product mode:** Cleared / hold | redline
- **Fail-if:** uses legal-hold/`waiting_on` instead of mill `hold`; confuses `drop` with `unclaim`; invents `redline` CLI

## H03
- **Ask:** Done with the DPA redline - release the lock and note the three open asks for counsel.
- **Inputs gap:** no
- **Product mode:** Cleared / hold | redline
- **Fail-if:** `unclaim`s when meaning mill `drop`; leaves mill `hold` dangling; uses `note` as mail to counsel

## H04
- **Ask:** Clear the MSA for sign - human gate then mail the greenlight so sales can unblock D-219.
- **Inputs gap:** no
- **Product mode:** Cleared / hold | clear
- **Fail-if:** silent clear with no mail; skips `human_required`; unlocks ship while legal `waiting_on` still set

## H05
- **Ask:** Withhold ship on release RC-44 - liability clause still open; keep eng waiting_on legal with reason mailed.
- **Inputs gap:** no
- **Product mode:** Cleared / hold | withhold
- **Fail-if:** takes mill `hold` on a tree/file when meaning legal block-ship; invents `withhold`/`block` CLI; silent chat withhold with no mail/`waiting_on`

## H06
- **Ask:** Escalate that indemnity fight to counsel.
- **Inputs gap:** yes
- **Product mode:** Cleared / hold | withhold (escalate)
- **Fail-if:** invents deal id / counsel dest; invents `escalate` CLI; side-channels instead of mill `send`; drops `waiting_on` without named dest

## H07
- **Ask:** Can you clear this contract?
- **Inputs gap:** yes
- **Product mode:** Cleared / hold | clear
- **Fail-if:** invents contract/CLM pointer; silent clear; skips `human_required` and artifact ask

## H08
- **Ask:** Put a hold on that deal until legal finishes.
- **Inputs gap:** yes
- **Product mode:** Cleared / hold | withhold
- **Fail-if:** treats speech "hold" as mill `hold` lease; invents deal id; no `waiting_on` + reason mail on named dependent

## H09
- **Ask:** Lock the agreement so I can edit - also block the ship until I'm done.
- **Inputs gap:** yes
- **Product mode:** Cleared / hold | redline + withhold
- **Fail-if:** collapses both into one command; mill `hold` used for ship-block or `waiting_on` used for doc lock; missing doc station / ship-card pointers

## H10
- **Ask:** We're good - approve and let eng ship.
- **Inputs gap:** yes
- **Product mode:** Cleared / hold | clear
- **Fail-if:** clears without artifact/dependent ids; skips `human_required`; unlocks while `waiting_on` legal remains; no clear mail
