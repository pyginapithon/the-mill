# Claim - Floor part fingerprints (Loop-2)

Status: **Release Candidate Ready** (throwaway A/B + pytest). Local commit only. No push / PyPI. No live ALTER lan/aws until Product GO.

## Lock

GET `/api/floor` with `fp=...` returns empty part payloads when unchanged; always echoes `fp`; HTTP 200; mill stamp unchanged. MySQL `mill_fp` owns hashes - client only round-trips.

## Before / after

| Poll | Before | After unchanged |
|------|--------|-----------------|
| mail,trees | full mailbox + trees | envelope + `fp` + empty `mailbox`/`trees`/`desk_unread` |

## Evidence

Path: `~/.mill/evidence/builder-floor-fingerprint-20260926/`

- `DESIGN.md` - design draft copy
- `ab-throwaway.txt` - apply_records + split_script A/B; hit/miss/hit2
- `pytest-floor-fp.txt` - `tests/server/records/test_floor_fp.py` (5 passed)
- `WALL-CONTRACT.md` - handoff for wall-ui
- `CLAIM-floor-fingerprint.md` - this claim

## Changed files

- `agent_coord/server/sql/fn_fp.sql` (new) - `mill_fp`
- `agent_coord/server/sql/apply_order.txt` - list `fn_fp.sql` after `fn_weight.sql`
- `agent_coord/server/sql/sp_floor_scope.sql` - add `mill_floor_fp`
- `agent_coord/server/records/floor.py` - parse fps; skip unchanged; emit `fp`
- `agent_coord/server/middleware.py` - pass qs `fp` / `fp_*`; include fp in floor cache key
- `tests/server/records/test_floor_fp.py` (new)
- `docs/claims/CLAIM-floor-fingerprint.md` (new)

## Acceptance checks (Builder)

1. Cold poll without `fp` -> full parts + `fp` map. **PASS** (ab-throwaway / pytest)
2. Immediate repeat with echoed `fp` -> empty mailbox/trees, `fp` identical, HTTP 200 path via records API. **PASS**
3. Insert mail -> next poll full for mail, new fp; trees fp stable. **PASS**
4. Open mail / trees mutate - covered by material design (opened/receipt in mail material; structure stats for trees). Unit path ready; open-mail bust left for Validator live if needed.
5. No ALTER on live - throwaway DB only. **PASS**

## Out of scope

- 304/ETag; wall_ui paint (Wall claim / WALL-CONTRACT.md)
- Live lan/aws SQL apply (needs separate Product GO after throwaway proof)

## Release Candidate Ready

- Version: 0.5.6 (unchanged pack; SQL apply on next host update)
- Claims summary: floor part fingerprints via MySQL `mill_fp` + `mill_floor_fp`; empty-on-unchanged; fp echo; Builder SoR only
- Recommended commit message: `Floor part fingerprints (Loop-2): mill_fp + empty-on-match.`
- Ready for Validator
