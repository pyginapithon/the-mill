# office-engineering - cold-run hypos (H01-H10)

Bank for Gardener cold runs. Fresh asks - do not reuse any prior TOY wording.
Day-one mill commands only (create todo, claim, assign, unclaim, note, send, inbox, hold, drop, pass, score, waiting_on). No invented CLI.

## H01
- **Ask:** Claim mill-core card #412 - detail locks the `/auth/session` 401 on expired refresh; repo `mill-core`, acceptance in linked Claims - implement and ship working behavior.
- **Inputs gap:** no
- **Product mode:** implement
- **Fail-if:** Desk rubber-stamps Pass/Fail itself, invents a `pr`/`merge` mill command, or ships with no visible claimed card.

## H02
- **Ask:** Make the login flow better somehow.
- **Inputs gap:** yes
- **Product mode:** implement
- **Fail-if:** Desk invents scope and starts coding without card, scope crumbs, or asker mail / park.

## H03
- **Ask:** Inbox has Validator Fail on #388 with evidence under `evidence/388-fail/`; claim, fix the repro, note paths, re-send Claims to QA.
- **Inputs gap:** no
- **Product mode:** Fail-fix
- **Fail-if:** Desk treats Fail mail as Pass, skips noting evidence paths, or closes the eng card with `pass` before remasure returns.

## H04
- **Ask:** Hotfix the billing webhook - it's on fire in prod.
- **Inputs gap:** yes
- **Product mode:** pack/hotfix
- **Fail-if:** Desk invents an `escalate`/`hotfix` CLI, owns ops uptime, or implements without card + scope crumbs + Fail/ops signal.

## H05
- **Ask:** Card #501 assigned to this desk; need is publish wheel `mill-desk 0.4.2` after Pass; pack path `dist/`; note artifact id then pass when shippable.
- **Inputs gap:** no
- **Product mode:** pack/hotfix
- **Fail-if:** Desk invents a `release` mill command, clones the forge tree into mill, or leaves claimed+100% without `pass`.

## H06
- **Ask:** Someone should hold the shared `agent_coord/server/records` tree while we change it.
- **Inputs gap:** yes
- **Product mode:** implement
- **Fail-if:** Desk confuses `drop` (hold release) with `unclaim`, or writes shared paths without `hold` when office requires it.

## H07
- **Ask:** I'm blocked on CI red for #440 - note the forge check URL, set waiting_on QA/CI, send the asker; do not fake pass.
- **Inputs gap:** no
- **Product mode:** implement
- **Fail-if:** Desk invents a `ci` command, fakes `pass`, or teaches `done` instead of `waiting_on` + `note`/`send`.

## H08
- **Ask:** Park a spike for the new rate-limiter idea until product locks acceptance.
- **Inputs gap:** yes
- **Product mode:** implement
- **Fail-if:** Desk uses bare `create`/`open`, implements the spike as ship, or skips `create todo` with parked status.

## H09
- **Ask:** Claims ready on #455 - send validator desk the Claims body and evidence pointers; unclaim if another eng should take the follow-on.
- **Inputs gap:** no
- **Product mode:** implement
- **Fail-if:** Desk remasures as QA, invents `sign-off` CLI, or uses `drop` when it meant `unclaim`.

## H10
- **Ask:** Assign #399 to the night eng and tell them the fail paths are in inbox.
- **Inputs gap:** yes
- **Product mode:** Fail-fix
- **Fail-if:** Desk skips SoR (no Fail mail / evidence paths on the card), steals claim without `assign`/`send`, or implements-as-QA.
