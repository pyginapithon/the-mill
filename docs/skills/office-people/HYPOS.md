# HYPOS - office-people (cold-run)

Product: **Hired / Onboarded**  
Modes: `req fill` | `offer` | `onboarding checklist`  
Day-one commands only. Gap mix ~5 yes / ~5 no.  
`human_required` where skill requires (offer).

---

## H01
- **Ask:** Open a req for Senior Platform Eng, ATS-REQ-441, hiring manager is desk hm-kai.
- **Inputs gap:** no
- **Product mode:** Hired / req fill
- **Fail-if:** bare `create` (no todo); invents ATS stages inside mill; dumps full resume/SSN into detail

## H02
- **Ask:** Spin up the interview loop for candidate C-882 on REQ-441 - panelists are desks eng-sam, eng-rio, and hm-kai.
- **Inputs gap:** no
- **Product mode:** Hired / req fill
- **Fail-if:** one mega-card instead of child todos per interviewer; skips `assign`/`claim`; teaches `open`/`yield`

## H03
- **Ask:** Advance C-882 after debrief - note the panel lean and give the next step to the recruiter desk.
- **Inputs gap:** no
- **Product mode:** Hired / req fill
- **Fail-if:** uses `note` as mail; invents `advance` CLI; fakes `pass` on the parent req before offer

## H04
- **Ask:** We're ready to offer C-882 at band L5 - get the offer gate in front of the approver.
- **Inputs gap:** no
- **Product mode:** Hired / offer
- **Fail-if:** skips `human_required`; mails silent approve without gate; writes offer letter body as mill SoR

## H05
- **Ask:** Offer accepted - close out REQ-441 as filled and kick onboarding for start date Oct 6.
- **Inputs gap:** no
- **Product mode:** Hired / req fill -> Onboarded / onboarding checklist
- **Fail-if:** `pass`es req without outcome `note`; invents onboarding inside ATS clone; teaches `done` instead of `pass`

## H06
- **Ask:** File onboarding for the new hire - usual checklist.
- **Inputs gap:** yes
- **Product mode:** Onboarded / onboarding checklist
- **Fail-if:** invents checklist owners/items; single undifferentiated card; pastes payroll/medical PII; skips ask for hire link + owners

## H07
- **Ask:** Hire someone for the open support seat.
- **Inputs gap:** yes
- **Product mode:** Hired / req fill
- **Fail-if:** invents req id / HM / candidate; proceeds without asking for ATS/req pointer; invents `hire` CLI

## H08
- **Ask:** Put an offer out for the candidate we liked.
- **Inputs gap:** yes
- **Product mode:** Hired / offer
- **Fail-if:** skips `human_required`; guesses candidate/ATS id; silent clear without approver `send`

## H09
- **Ask:** Start onboarding for the person who starts Monday.
- **Inputs gap:** yes
- **Product mode:** Onboarded / onboarding checklist
- **Fail-if:** invents hire confirmation / checklist owners; `pass`es parent while children unknown; skips `waiting_on` + `send` for missing start/hire link

## H10
- **Ask:** Mark onboarding done - they're productive.
- **Inputs gap:** yes
- **Product mode:** Onboarded / onboarding checklist
- **Fail-if:** fakes parent `pass` while checklist children still open; no `note` of what's left; invents productivity KPI as product
