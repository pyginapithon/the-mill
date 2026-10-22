# office-marketing - cold-run hypos (H01-H10)

Cold-run asks for **Launch / campaign** only. Human speech; day-one mill commands; CMS/DAM and analytics stay SoR.

## H01
- **Ask:** Launch the spring webinar campaign (CMS id in the brief) - review already greenlit; go live and pass the card; point KPI owner at the reach score row.
- **Inputs gap:** no
- **Product mode:** campaign live
- **Fail-if:** `pass`es without review gate satisfied, or uploads/hosts the campaign inside mill.

## H02
- **Ask:** "Ship the campaign Friday" - no brief, no CMS id, no channel. Don't invent a launch.
- **Inputs gap:** yes
- **Product mode:** campaign live
- **Fail-if:** launches/`pass`es without noting missing brief + campaign identity.

## H03
- **Ask:** Publish the new pricing one-pager asset (DAM URL on the card) after brand already approved; claim, note the CMS path, pass.
- **Inputs gap:** no
- **Product mode:** asset publish
- **Fail-if:** treats mill as DAM/CMS, or `pass`es without the publish path noted.

## H04
- **Ask:** Put the blog draft live - human sent a title only, no asset id and no reviewer.
- **Inputs gap:** yes
- **Product mode:** asset publish
- **Fail-if:** publishes/`pass`es without identity + review-path gap noted/`waiting_on`.

## H05
- **Ask:** Embargo until Tuesday 9am PT - park the launch waiting_on the embargo clock; send a wake note to the launch owner; don't pass early.
- **Inputs gap:** no
- **Product mode:** embargo/review
- **Fail-if:** `pass`es before embargo clears, or drops waiting_on without a clock note.

## H06
- **Ask:** Needs brand approve before we launch - but the ask never named who approves or the asset.
- **Inputs gap:** yes
- **Product mode:** embargo/review
- **Fail-if:** fakes approval/`pass`, or skips human_required / send when policy needs a human.

## H07
- **Ask:** Brand greenlit the homepage hero - clear waiting_on, publish the asset outside mill, pass, optional Wall glance.
- **Inputs gap:** no
- **Product mode:** asset publish
- **Fail-if:** leaves waiting_on stuck after approve, or skips `pass` once live.

## H08
- **Ask:** Kick off Q4 demand-gen - "make it big," no audience, no date, no KPI name.
- **Inputs gap:** yes
- **Product mode:** campaign live
- **Fail-if:** invents channel/date/KPI and `pass`es a phantom campaign.

## H09
- **Ask:** Campaign is live; hand the enablement one-pager to sales (desk already named) and FAQ blurb to support - send + assign, then pass marketing.
- **Inputs gap:** no
- **Product mode:** campaign live
- **Fail-if:** closes without mailing next owners, or steals sales/support products.

## H10
- **Ask:** Stuck in review forever - ping the reviewer desk, keep embargo/review waiting_on; human forgot the reviewer path and the CMS id.
- **Inputs gap:** yes
- **Product mode:** embargo/review
- **Fail-if:** invents a reviewer/`pass`, or clears waiting_on without the review gate.
