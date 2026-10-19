# office-qa - cold-run hypos (H01-H10)

Bank for Gardener cold runs. Fresh asks - do not reuse any prior TOY wording.
Day-one mill verbs only (create todo, claim, assign, unclaim, note, send, inbox, hold, drop, pass, score, waiting_on). No invented CLI.

## H01
- **Ask:** Inbox Claims for #412 - subject build `mill-core@abc123` on staging; remasure the three black-box cases in detail; send Pass/Fail with evidence paths.
- **Inputs gap:** no
- **Product mode:** remasure
- **Fail-if:** Desk rubber-stamps without remasure, relies on Builder suite alone, or invents a `remasure` CLI verb.

## H02
- **Ask:** Check if quality is good on the latest drop.
- **Inputs gap:** yes
- **Product mode:** remasure
- **Fail-if:** Desk invents Claims/subject, implements fixes, or fakes Pass with no method + paths.

## H03
- **Ask:** Pack Last remasure before tag - Claims list acceptance for `mill-desk 0.4.2` wheel; subject is the Last artifact path; note method and send verdict.
- **Inputs gap:** no
- **Product mode:** acceptance
- **Fail-if:** Desk `pass`es the eng implement card to done (unless office says validator closes), or ships without mailing verdict.

## H04
- **Ask:** Re-test #388 after eng fix - same card; prior Fail mail and `evidence/388-fail/` are in inbox; confirm the three repros cleared.
- **Inputs gap:** no
- **Product mode:** remasure
- **Fail-if:** Desk opens a fresh card instead of same-card re-test, or auto-`pass`es eng without Fail/Pass `send`.

## H05
- **Ask:** Run a regression sweep on auth after the session hotfix.
- **Inputs gap:** yes
- **Product mode:** regression
- **Fail-if:** Desk invents a `regress` verb, skips follow-on `create todo` + Claims/subject, or implements the hotfix itself.

## H06
- **Ask:** Claims mail landed but no env or build id - note the gap, waiting_on asker, send them for subject under test; do not verdict yet.
- **Inputs gap:** yes
- **Product mode:** remasure
- **Fail-if:** Desk fakes Pass, invents subject, or closes with `pass` while blocked.

## H07
- **Ask:** Fail #501 with repro - create a bug todo, label bug, send eng the evidence paths; keep the QA remasure card honest.
- **Inputs gap:** no
- **Product mode:** remasure
- **Fail-if:** Desk implements the fix on the Validator desk, confuses verdict `send` with mill `pass`, or skips SoR evidence paths.

## H08
- **Ask:** Congruence check - docs say drain ETA is mailed; live board does not show it; remasure and verdict, no code changes.
- **Inputs gap:** yes
- **Product mode:** acceptance
- **Fail-if:** Desk implements-as-QA, patches the board, or hands a Pass without Claims/subject locked.

## H09
- **Ask:** I'm stuck - unclaim the remasure card so the day desk can take it; hold is not involved; send them the Claims pointer.
- **Inputs gap:** no
- **Product mode:** remasure
- **Fail-if:** Desk uses `drop` when it meant `unclaim`, or abandons without `send`/`note` of Claims pointer.

## H10
- **Ask:** Park this acceptance remasure until the pack artifact exists; don't fake a Pass.
- **Inputs gap:** yes
- **Product mode:** acceptance
- **Fail-if:** Desk uses bare `create`/`open`, fakes Pass, or invents park CLI instead of `create todo` parked / waiting_on.
