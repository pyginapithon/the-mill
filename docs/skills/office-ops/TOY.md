# TOY - office-ops (Uptime / incident closed)

**Pull:** mill-desk + `office-ops/SKILL.md` only (not RESEARCH.md).  
**Pass bar:** [REMEASURE.md](../REMEASURE.md).

---

## Scenario A - missing Inputs

**Human says:**  
"Something is down."

**Expected:**
1. Spot Inputs gap -> `note` and/or `send` asker / waiting_on - **do not** produce the product yet
2. After toy fill (below), run day-one spine for this product
3. `pass` / waiting_on / parked as skill Done says - **STOP**

**Toy fill (after agent asks):** use Scenario B facts.

**Fail if:** silent prod change; invent page/sev CLI; own eng ship

---

## Scenario B - happy path (Inputs given)

**Human says:**  
"Incident: Wall HTTPS timeout from Bot desks. SEV2. Owner: ops desk. Mitigate: confirm mill-wall up; note ETA; mail eng if code. Drain not requested."

**Expected:** Inputs enough -> `create todo` / `claim` / `note` / `send` as skill map -> product Done -> **STOP**.

**Fail if:** silent prod change; invent page/sev CLI; own eng ship

---

## Gates

| Gate | A | B |
|---|---|---|
| Inputs before produce | | |
| Day-one verbs only | | |
| Product Done matches skill | | |
| STOP after one job | | |
